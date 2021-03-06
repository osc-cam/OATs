import csv
import datetime
import dateutil.parser
import logging
import logging.config
import os
import re
import sys

import common.cufs as cufs
# from . import cufs
from common.oatsutils import extract_csv_header, output_debug_csv, prune_and_cleanup_string, DOI_CLEANUP, DOI_FIX
# from .oatsutils import extract_csv_header, output_debug_csv, prune_and_cleanup_string, DOI_CLEANUP, DOI_FIX
from common.midas_constants import RCUK_FORMAT_COST_CENTRE_SOF_COMBOS, APC_TRANSACTION_CODES, OTHER_PUB_CHARGES_TRANSACTION_CODES

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
# logger.addHandler(ch)


# Use this dictionary to force the mapping of particularly problematic oa numbers to zd numbers. For example,
# both ZD tickets 6127 and 9693 have external ID set to OA-2629, so we need to map this one manually to the
# correct zd_ticket
MANUAL_OA2ZD_DICT = {
    'OA-1267':'3965',
    'OA-2208':'5466',
    'OA-2629':'6127',
    'OA-2669':'6202',
    'OA-2746':'6331',
    'OA-3194':'7104',
    'OA-4299':'9020',
    'OA-4658':'9660',
    'OA-4998':'10229',
    'OA-5555':'11066',
    'OA-5620':'11167',
    'OA-6514':'13035',
    'OA-8663':'17157',
    'OA-9922':'26755',
    }

unmatched_payment_file_prefix = 'Midas_debug_payments_not_matched_to_zd_numbers__'
nonJUDB_payment_file_prefix = 'Midas_debug_non_JUDB_payments__'
nonEBDU_payment_file_prefix = 'Midas_debug_non_EBDU_EBDV_or_EBDW_payments__'

def output_pruned_zendesk_export(zenexport, output_filename, **kwargs):
    '''
    This function filters a CSV export from Zendesk, excluding any tickets matching kwargs
    :param zenexport: the CSV file exported from Zendesk
    :param output_filename: the name of the file we will save pruned data to
    :param kwargs: a dictionary where k are Zendesk field names and v are lists of values to exclude
    '''
    p = Parser(zenexport)
    p.index_zd_data()
    fieldnames = p.zenexport_fieldnames
    with open(output_filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writeheader()
        for _, ticket in p.zd_dict.items():
            output_ticket = False
            for field, values in kwargs.items():
                for value in values:
                    if ticket.metadata[field] != value:
                        output_ticket = True
            if output_ticket:
                writer.writerow(ticket.metadata)

def filter_zendesk_export(zenexport, output_filename, match_type='or', **kwargs):
    '''
    This function filters a CSV export from Zendesk, outputing only tickets that match kwargs
    :param zenexport: the CSV file exported from Zendesk
    :param output_filename: the name of the file we will save pruned data to
    :param match_type: if 'or' tickets matching any kwarg will be included in output;
            if 'and' tickets matching all kwargs will be included in output
    :param kwargs: a dictionary where k are Zendesk field names and v are values to include
    '''
    p = Parser(zenexport)
    p.index_zd_data()
    fieldnames = p.zenexport_fieldnames
    with open(output_filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writeheader()
        ticket_counter = 0
        for _, ticket in p.zd_dict.items():
            ticket_counter += 1
            logger.debug('Working on ticket {} of {}'.format(ticket_counter, zenexport))
            if match_type == 'or':
                output_ticket = False
                for field, values in kwargs.items():
                    logger.debug('kwargs fields and values: {}: {};'.format(field, values))
                    logger.debug('ticket.metadata[{}]: {}'.format(field, ticket.metadata[field]))
                    if type(values) not in [type([1,2,3]), type((1,2,3))]:
                        values = [values]
                    for value in values:
                        if ticket.metadata[field].lower().strip() == str(value).lower().strip():
                            output_ticket = True
                            logger.debug("Value of ticket metadata ({}) "
                                         "matches query ({})".format(ticket.metadata[field], value))
                        else:
                            logger.debug("Value of ticket metadata ({}) does not "
                                         "match query ({})".format(ticket.metadata[field], value))
            elif match_type == 'and':
                output_ticket = True
                for field, values in kwargs.items():
                    if type(values) not in [type([1,2,3]), type((1,2,3))]:
                        values = [values]
                    for value in values:
                        if ticket.metadata[field] != value:
                            output_ticket = False
            if output_ticket:
                writer.writerow(ticket.metadata)

class ZdFieldsMapping():
    '''
    A mapping of current Zendesk field names.
    Used to faciliate updating OATs when ZD field names are updated.
    '''
    def __init__(self):
        self.apc_payment = 'Is there an APC payment? [list]'
        self.coaf_payment = 'COAF payment [flag]'
        self.coaf_policy = 'COAF policy [flag]'
        self.doi = '#DOI (like 10.123/abc456) [txt]'
        self.duplicate = 'Duplicate [flag]'
        self.duplicate_of = 'Duplicate of (ZD-123456) [txt]'
        self.embargo = 'Embargo duration [list]'
        self.external_id = '#externalID [txt]'
        self.green_allowed_version = 'Green allowed version [list]'
        self.green_licence = 'Green licence [list]'
        self.id = 'Id'
        self.manuscript_title = '#Manuscript title [txt]'
        self.publication_date = '#Publication date (YYYY-MM-DD) [txt]'
        self.rcuk_payment = 'RCUK payment [flag]'
        self.rcuk_policy = 'RCUK policy [flag]'
        self.repository_link = '#Repository link [txt]'

        self.summation_column = 'Summation column'
        self.requester = 'Requester'
        self.requester_id = 'Requester id'
        self.requester_external_id = 'Requester external id'
        self.requester_email = 'Requester email'
        self.requester_domain = 'Requester domain'
        self.submitter = 'Submitter'
        self.assignee = 'Assignee'
        self.group = 'Group'
        self.subject = 'Subject'
        self.tags = 'Tags'
        self.status = 'Status'
        self.priority = 'Priority'
        self.via = 'Via'
        self.ticket_type = 'Ticket type'
        self.created_at = 'Created at'
        self.updated_at = 'Updated at'
        self.assigned_at = 'Assigned at'
        self.organization = 'Organization'
        self.due_date = 'Due date'
        self.initially_assigned_at = 'Initially assigned at'
        self.solved_at = 'Solved at'
        self.resolution_time = 'Resolution time'
        self.satisfaction_score = 'Satisfaction Score'
        self.group_stations = 'Group stations'
        self.assignee_stations = 'Assignee stations'
        self.reopens = 'Reopens'
        self.replies = 'Replies'
        self.first_reply_time_in_minutes = 'First reply time in minutes'
        self.first_reply_time_in_minutes_within_business_hours = 'First reply time in minutes within business hours'
        self.first_resolution_time_in_minutes = 'First resolution time in minutes'
        self.first_resolution_time_in_minutes_within_business_hours = 'First resolution time in minutes within business hours'
        self.full_resolution_time_in_minutes = 'Full resolution time in minutes'
        self.full_resolution_time_in_minutes_within_business_hours = 'Full resolution time in minutes within business hours'
        self.agent_wait_time_in_minutes = 'Agent wait time in minutes'
        self.agent_wait_time_in_minutes_within_business_hours = 'Agent wait time in minutes within business hours'
        self.requester_wait_time_in_minutes = 'Requester wait time in minutes'
        self.requester_wait_time_in_minutes_within_business_hours = 'Requester wait time in minutes within business hours'
        self.on_hold_time_in_minutes = 'On hold time in minutes'
        self.on_hold_time_in_minutes_within_business_hours = 'On hold time in minutes within business hours'
        self.jira_sharing = 'JIRA Sharing [list]'
        self.query = 'Query [flag]'
        self.wrong_version = 'Wrong version [flag]'
        self.department = 'Department [txt]'
        self.corresponding_author = 'Corresponding author [txt]'
        self.corresponding_author_institution = 'Corresponding author institution [txt]'
        self.journal_title = 'Journal title [txt]'
        self.publisher = 'Publisher [txt]'
        self.other_funder_policies = 'Other funder policies [flag]'
        self.other_institution_payment = 'Other institution payment [flag]'
        self.grant_payment = 'Grant payment [flag]'
        self.vouchermembershipoffset_payment = 'Voucher/membership/offset payment [flag]'
        self.authordepartment_payment = 'Author/department payment [flag]'
        self.repository_status = 'Repository status [list]'
        self.manuscript_deposit_apollo = 'Manuscript deposit (Apollo) [flag]'
        self.manuscript_deposit_pmc_other = 'Manuscript deposit (PMC; other) [flag]'
        self.apc_payment_from_block_grants = 'APC payment from block grants [flag]'
        self.hefce_exception = 'HEFCE exception [flag]'
        self.hefce_failure = 'HEFCE failure [flag]'
        self.retrospective_accepted_preapril_2016 = 'Retrospective (accepted pre-April 2016) [flag]'
        self.no_further_action = 'No further action [flag]'
        self.apc_charged_to_rcuk_ebdu = 'APC charged to RCUK (EBDU) [dec]'
        self.apc_charged_to_coaf_ebdu = 'APC charged to COAF (EBDU) [dec]'
        self.pagecolour_charges__rcuk_ebdw = 'Page/colour charges - RCUK (EBDW) [dec]'
        self.membership_fees__rcuk_ebdv = 'Membership fees - RCUK (EBDV) [dec]'
        self.purchase_order_number = 'Purchase order number [txt]'
        self.total_amount_invoiced_apc = 'Total amount invoiced (APC) [dec]'
        self.total_amount_invoiced_pagecolour = 'Total amount invoiced (Page/Colour) [dec]'
        self.apc_invoice_number = 'APC invoice number [txt]'
        self.oa_approved_via_prepayment_deal = 'OA approved via prepayment deal [flag]'
        self.original_commitment__rcuk = 'Original commitment - RCUK [dec]'
        self.original_commitment__coaf = 'Original commitment - COAF [dec]'
        self.outstanding_commitment__rcuk__inc_vat = 'Outstanding commitment - RCUK (£ inc. VAT) [dec]'
        self.outstanding_commitment__coaf__inc_vat = 'Outstanding commitment - COAF (£ inc. VAT) [dec]'
        self.amount_paid__rcuk = 'Amount paid - RCUK [dec]'
        self.amount_paid__coaf = 'Amount paid - COAF [dec]'
        self.total_expenditure__rcuk = 'Total expenditure - RCUK [dec]'
        self.total_expenditure__coaf = 'Total expenditure - COAF [dec]'
        self.total_expenditure__wellcome = 'Total expenditure - Wellcome [dec]'
        self.published = 'Published [flag]'
        self.published_online = 'Published online [flag]'
        self.compliant__coaf = 'Compliant - COAF [flag]'
        self.compliant__hefce = 'Compliant - HEFCE [flag]'
        self.compliant__rcuk = 'Compliant - RCUK [flag]'
        self.compliant__other = 'Compliant - Other [flag]'
        self.open_access_on_publishers_site = "Open access on publisher's site? [flag]"
        self.is_open_access_obvious = 'Is Open Access obvious? [list]'
        self.correct_licence_clearly_labelled = 'Correct licence clearly labelled? [flag]'
        self.awaiting_author_response = 'Awaiting author response [flag]'
        self.manuscript_download_link = 'Manuscript download link [txt]'
        self.awaiting_publisher_response = 'Awaiting publisher response [flag]'
        self.invoicing = 'Invoicing [flag]'
        self.test = 'Test [flag]'
        self.accepted_in_last_3_months = 'Accepted in last 3 months [flag]'
        self.not_yet_accepted = 'Not Yet Accepted [flag]'
        self.wellcome_payment = 'Wellcome payment [flag]'
        self.selfbilled_vat__wellcome = 'Self-billed VAT - Wellcome [dec]'
        self.erc = 'ERC [flag]'
        self.awarding_institution = 'Awarding institution [txt]'
        self.impersonator_email_address = 'Impersonator email address [txt]'
        self.internal_item_id_apollo = 'Internal Item ID (Apollo) [txt]'
        self.symplectic_acceptance_date_yyyymmdd = 'Symplectic acceptance date (YYYY-MM-DD) [txt]'
        self.nspn_dataset = 'NSPN Dataset [flag]'
        self.arthritis_research_uk = 'Arthritis Research UK [flag]'
        self.date_deposit_completed_yyyymmdd = 'Date deposit completed (YYYY-MM-DD) [txt]'
        self.oasis_type = 'OASIS type [list]'
        self.legacy_thesis = 'Legacy Thesis [flag]'
        self.breast_cancer_now_breast_cancer_campaign = 'Breast Cancer Now (Breast Cancer Campaign) [flag]'
        self.college = 'College [txt]'
        self.thesis_access_level = 'Thesis access level [list]'
        self.date_publisher_fulfilled_funder_requirements_yyyymmdd = 'Date publisher fulfilled funder requirements (YYYY-MM-DD) [txt]'
        self.apc_charged_to_wellcome_supplement_ebdu = 'APC Charged to Wellcome Supplement (EBDU) [dec]'
        self.date_compliance_first_checked_yyyymmdd = 'Date compliance first checked (YYYY-MM-DD) [txt]'
        self.rcuk_cost_centre = 'RCUK cost centre [list]'
        self.membership_fee_paid_on_cufs = 'Membership fee paid on CUFS [flag]'
        self.parkinsons_uk = "Parkinson's UK [flag]"
        self.hero_thesis = 'Hero Thesis [flag]'
        self.dspace_tickets = 'DSpace Tickets [flag]'
        self.zd_ticket_number_of_original_submission_zd123456 = 'ZD ticket number of original submission (ZD-123456) [txt]'
        self.crsid = 'CRSid [txt]'
        self.thesis_deposit_status = 'Thesis deposit status [list]'
        self.new_thesis = 'New Thesis [flag]'
        self.outstanding_commitment_wellcome_supplement = 'Outstanding Commitment (Wellcome Supplement) [dec]'
        self.access_exception_type = 'Access exception type [list]'
        self.apc_already_paid = 'APC already paid? [flag]'
        self.esrc = 'ESRC [flag]'
        self.coaf_failure = 'COAF failure [flag]'
        self.exception_type = 'Exception type [list]'
        self.request_a_copy_article = 'Request a Copy (Article) [flag]'
        self.data_deposition_status = 'Data deposition status [list]'
        self.request_a_copy_action = 'Request a Copy Action [list]'
        self.nerc = 'NERC [flag]'
        self.thesis_request__digitised_nonpublic = 'Thesis Request - digitised, non-public [flag]'
        self.rcuk_funding = 'RCUK Funding [flag]'
        self.bloodwise_leukaemia__lymphoma_research = 'Bloodwise (Leukaemia & Lymphoma Research) [flag]'
        self.technical_exception_type = 'Technical exception type [list]'
        self.rcukcoaf_failure_action = 'RCUK/COAF failure action [list]'
        self.edit_existing_repository_record = 'Edit existing repository record [flag]'
        self.pagecolour_invoice_processed = 'Page/colour invoice processed [flag]'
        self.epsrc_data_requirement = 'EPSRC Data Requirement [flag]'
        self.membership_invoice_processed = 'Membership invoice processed [flag]'
        self.unmediated_deposit_type = 'Unmediated deposit type [list]'
        self.thesis_embargo_reason_other = 'Thesis embargo reason other [txt]'
        self.hefce_transitional_deadline_met = 'HEFCE transitional deadline met [flag]'
        self.dspace_done__needs_email = 'DSpace done - needs email [flag]'
        self.wrong_version_type = 'Wrong version type [list]'
        self.published = 'published [flag]'
        self.corresponding_authors_affiliations = "Corresponding author(s)' affiliation(s) [list]"
        self.promote_on_twitter = 'Promote on Twitter? [flag]'
        self.sensitive_information_clearance = 'Sensitive information clearance [list]'
        self.external_email_address = 'External email address [txt]'
        self.pagecolour_invoice_number = 'Page/colour invoice number [txt]'
        self.any_problems_with_the_publisher = 'Any problems with the publisher? [flag]'
        self.membership_invoice_number = 'Membership invoice number [txt]'
        self.bbsrc_data_requirement = 'BBSRC Data Requirement [flag]'
        self.fp7 = 'FP7 [flag]'
        self.thesis_request__not_digitised = 'Thesis Request - not digitised [flag]'
        self.what_did_the_publisher_do_wrong = 'What did the publisher do wrong? [txt]'
        self.university_student_number_usn = 'University Student Number (USN) [txt]'
        self.apc_fee_paid_on_cufs = 'APC fee paid on CUFS [flag]'
        self.online_publication_date_yyyymmdd = 'Online Publication Date (YYYY-MM-DD) [txt]'
        self.dataset_embargoed = 'Dataset embargoed [flag]'
        self.degree = 'Degree [txt]'
        self.nihr = 'NIHR [flag]'
        self.apc_invoice_paid = 'APC invoice paid [flag]'
        self.tweeted = 'Tweeted [flag]'
        self.technical_issue = 'Technical Issue [flag]'
        self.other_exception_type = 'Other exception type [list]'
        self.commitment_note = 'Commitment note [txt]'
        self.publication_type = 'publication type [list]'
        self.pagecolour_fee_paid_on_cufs = 'Page/colour fee paid on CUFS [flag]'
        self.date_added_to_apollo_yyyymmdd = 'Date added to Apollo (YYYY-MM-DD) [txt]'
        self.placeholder_dataset = 'Placeholder dataset [flag]'
        self.data__sensitiveconfidential_information = 'Data - sensitive/confidential information? [flag]'
        self.compliance_checking_status = 'Compliance checking status [list]'
        self.no_raw_data_included = 'No raw data included [flag]'
        self.invoice_date_yyyymmdd = 'Invoice date (YYYY-MM-DD) [txt]'
        self.repository_feature_request = 'Repository feature request [flag]'
        self.type_of_request = 'Type of request? [list]'
        self.h2020 = 'H2020 [flag]'
        self.gold_team = 'Gold team [list]'
        self.hefce_out_of_scope = 'HEFCE Out of Scope [flag]'
        self.thesis_embargo_reason = 'Thesis embargo reason [txt]'
        self.twitter_handles = 'Twitter handles [txt]'
        self.thesis_contains_sensitive_information = 'Thesis contains sensitive information [flag]'
        self.in_dark_collection = 'In Dark Collection [flag]'
        self.data_supporting_a_publication = 'Data supporting a publication? [flag]'
        self.rcuk_failure = 'RCUK failure [flag]'
        self.thesis_title = 'Thesis title [txt]'
        self.ahrc = 'AHRC [flag]'
        self.licence_applied_by_publisher = 'Licence applied by publisher [list]'
        self.publication_in_apollo = 'Publication in Apollo [flag]'
        self.sword_deposit_thesis = 'SWORD Deposit Thesis [flag]'
        self.coaf_cost_centre = 'COAF cost centre [list]'
        self.membership_fees__coaf_ebdv = 'Membership fees - COAF (EBDV) [dec]'
        self.bbsrc = 'BBSRC [flag]'
        self.accessible_to_peerreviewers = 'Accessible to peer-reviewers? [flag]'
        self.autoreply_options = 'Auto-reply options [flag]'
        self.coaf_grant_numbers = 'COAF Grant Numbers [txt]'
        self.epsrc = 'EPSRC [flag]'
        self.request_a_copy_link = 'Request a copy link [txt]'
        self.wellcome_supplement_payment = 'Wellcome Supplement Payment [flag]'
        self.qualification_level = 'Qualification level [list]'
        self.mrc = 'MRC [flag]'
        self.apc_invoice_processed = 'APC invoice processed [flag]'
        self.is_this_an_ethics_query = 'Is this an ethics query? [flag]'
        self.dark_collection_status = 'Dark collection status [list]'
        self.supporting_article_doi = 'Supporting article DOI [txt]'
        self.thesis_source = 'Thesis source [list]'
        self.deposit_exception_type = 'Deposit exception type [list]'
        self.gates_foundation = 'Gates Foundation [flag]'
        self.stfc = 'STFC [flag]'
        self.request_a_copy_thesis = 'Request a Copy (Thesis) [flag]'
        self.thesis_embargo = 'Thesis Embargo [list]'
        self.degree_title = 'Degree title [txt]'
        self.feedback = 'Feedback [flag]'
        self.cancer_research_uk = 'Cancer Research UK [flag]'
        self.mrc_core_grant_payment = 'MRC core grant payment [flag]'
        self.dataset_title = 'Dataset title [txt]'
        self.symplectic_item_type = 'Symplectic item type [txt]'
        self.symplectic_impersonator = 'Symplectic impersonator [flag]'
        self.wellcome_trust = 'Wellcome Trust [flag]'
        self.british_heart_foundation = 'British Heart Foundation [flag]'
        self.repository_workflow_task = 'Repository workflow task [flag]'
        self.request_a_copy_data = 'Request a Copy (Data) [flag]'

    def parse_zd_fieldnames(zenexport):
        '''
        Parse fieldnames in zenexport and output a text file mapping fields to suggested class attributes.
        Used as a one-off aid when writing class ZdFieldsMapping
        '''
        regex = re.compile(r'\[\w+\]')
        symbols = re.compile(r'[^a-zA-Z0-9_ ]')
        with open('parsed_fieldnames.txt', 'w') as out:
            with open(zenexport) as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                for field in header:
                    a = re.sub(regex, '', field)
                    b = re.sub(symbols, '', a)
                    out_str = "    self.{} = '{}'\n".format(b.replace(' ', '_').lower().rstrip('_'), field)
                    out.write(out_str)


class Ticket():
    '''
    A single Zendesk ticket
    '''
    def __init__(self):
        '''
        :param self.metadata: data stored in Zendesk about this ticket
        :param self.rcuk_apc: APC amount charged to RCUK block grant
        :param self.rcuk_other: Amount of other publication fees charged to RCUK block grant
        :param self.decision_score: Integer indicating how likely this ticket is to contain a decision on policies
                and payments
        '''
        self.apc_grand_total = 0
        self.other_grand_total = 0
        self.apollo_handle = None
        self.article_title = None
        self.coaf_apc_total = 0
        self.coaf_other_total = 0
        self.coaf_payment = None
        self.coaf_policy = None
        self.decision_score = 0
        self.doi = None
        self.external_id = None
        self.dup_of = None
        self.number = None
        self.publication_date = None
        self.rcuk_apc_total = 0
        self.rcuk_other_total = 0
        self.rcuk_payment = None
        self.rcuk_policy = None
        self.invoice_apc = None
        self.invoice_page = None
        self.invoice_membership = None
        self.metadata = {}

    def output_metadata_as_csv(self, outcsv):
        fieldnames = self.metadata.keys()
        if not os.path.exists(outcsv):
            with open(outcsv, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
        with open(outcsv, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(self.metadata)

    def output_payment_summary_as_csv(self, outcsv):
        columns_mapping = [
            ['ZD number', self.number],
            ['OA/SE number', self.external_id],
            ['Article title', self.article_title],
            ['DOI', self.doi],
            ['APC total', self.apc_grand_total],
            ['Other total', self.other_grand_total],
            ['COAF total', self.coaf_apc_total],
            ['RCUK apc', self.rcuk_apc_total],
            ['RCUK other', self.rcuk_other_total],
            ['Zendesk data', '{}'.format(self.metadata)],
        ]
        if not os.path.exists(outcsv):
            with open(outcsv, 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([a[0] for a in columns_mapping])
        with open(outcsv, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([a[1] for a in columns_mapping])

class Parser():
    '''
    Parser for Zendesk CSV exports.
    Use this class to read in data exported from Zendesk and parse it into a number of
    dictionaries.
    '''
    def __init__(self, zenexport):
        self.apollo2zd_dict = {}
        self.cufs_map = None
        self.doi2zd_dict = {}
        self.oa2zd_dict = {}
        self.parsed_payments = {}
        self.grant_report = {}
        self.grant_report_requester = None
        self.grant_report_start_date = None
        self.grant_report_end_date = None
        self.invoice2zd_dict = {}
        self.output_map = None
        self.rejected_payments = {}
        self.title2zd_dict = {}
        self.title2zd_dict_COAF = {}
        self.title2zd_dict_RCUK = {}
        self.zd2oa_dups_dict = {}
        self.zd2zd_dict = {}
        self.zd_dict = {}
        self.zd_dict_COAF = {}
        self.zd_dict_RCUK = {}
        self.zd_dict_with_payments = {}
        self.zd_fields = ZdFieldsMapping()
        self.zenexport = zenexport
        self.zenexport_fieldnames = None

    def index_zd_data(self):
        """ This function parses a csv file exported from the UoC OSC zendesk account
            and returns several dictionaries with the contained data

            :param self.zenexport: path of the csv file exported from zendesk
            :param zd_dict: dictionary of Ticket objects indexed by zendesk ticket number (one Ticket object per number)
            :param title2zd_dict: dictionary of Ticket objects indexed by publication titles (list of objects per title)
            :param doi2zd_dict: dictionary of Ticket objects indexed by DOIs (list of objects per DOI)
            :param oa2zd_dict: dictionary of Ticket objects indexed by OA- numbers (list of objects per OA- number)
            :param apollo2zd_dict: dictionary of Ticket objects indexed by Apollo handles (list of objects per handle)
            :param zd2zd_dict: dictionary matching zendesk numbers to zendesk numbers IS THIS USED ANYWHERE?
            :return: zd_dict, title2zd_dict, doi2zd_dict, oa2zd_dict, apollo2zd_dict, zd2zd_dict
        """

        def convert_date_str_to_yyyy_mm_dd(string, dateutil_options):
            '''
            Function to convert dates to format YYYY-MM-DD
            :param string: original date string
            :param dateutil_options: options to be passed to dateutil
            :return: converted date or empty string if failed to convert
            '''
            try:
                d = dateutil.parser.parse(string, dateutil_options)
            except ValueError:
                d = datetime.datetime(1, 1, 1)
            d = d.strftime('%Y-%m-%d')
            if d == '1-01-01':
                return ('')
            else:
                return (d)

        def initiate_or_append_list(v_list, dict, zd_number):
            # logger.debug('v_list: {}'.format(v_list))
            for value in v_list:
                if value not in ['', '-']:
                    if value in dict.keys():
                        dict[value].append(zd_number)
                    else:
                        dict[value] = [zd_number]

        logger.info('Indexing Zendesk data')
        t_oa = re.compile("OA[ \-]?[0-9]{4,8}")
        with open(self.zenexport, encoding = "utf-8") as csvfile:
            # header_reader = csv.reader(csvfile)
            # self.zenexport_fieldnames = next(header_reader)
            reader = csv.DictReader(csvfile)
            self.zenexport_fieldnames = next(reader).keys()
            for row in reader:
                t = Ticket()  # create a new Ticket object
                t.number = row[self.zd_fields.id]
                t.dup_of = row[self.zd_fields.duplicate_of]
                t.external_id = row[self.zd_fields.external_id]
                t.article_title = row[self.zd_fields.manuscript_title].upper()
                t.rcuk_payment = row[self.zd_fields.rcuk_payment]
                t.rcuk_policy = row[self.zd_fields.rcuk_policy]
                t.coaf_payment = row[self.zd_fields.coaf_payment]
                t.coaf_policy = row[self.zd_fields.coaf_policy]
                t.invoice_apc = row[self.zd_fields.apc_invoice_number]
                t.invoice_page = row[self.zd_fields.pagecolour_invoice_number]
                t.invoice_membership = row[self.zd_fields.membership_invoice_number]
                t.apollo_handle = row[self.zd_fields.repository_link].replace('https://www.repository.cam.ac.uk/handle/' , '')
                t.doi = prune_and_cleanup_string(row[self.zd_fields.doi], DOI_CLEANUP, DOI_FIX)
                row[self.zd_fields.doi] = t.doi
                dateutil_options = dateutil.parser.parserinfo(dayfirst=True)
                t.publication_date = convert_date_str_to_yyyy_mm_dd(row[self.zd_fields.publication_date], dateutil_options)
                row[self.zd_fields.publication_date] = t.publication_date

                # Old OA- tickets (created before October 2014) do not have field external_id populated, so check if
                # subject line contains OA- reference number
                if (t.external_id in ['', '-']) and (row[self.zd_fields.subject][:23] == 'Open Access enquiry OA-'):
                    t.external_id = row[self.zd_fields.subject][20:]

                for v, dict in [
                        ([t.apollo_handle], self.apollo2zd_dict),
                        ([t.article_title], self.title2zd_dict),
                        ([t.doi], self.doi2zd_dict),
                        ([t.external_id], self.oa2zd_dict),
                        ([
                            row[self.zd_fields.apc_invoice_number].lower(),
                            row[self.zd_fields.pagecolour_invoice_number].lower(),
                            row[self.zd_fields.membership_invoice_number].lower()
                          ], self.invoice2zd_dict)
                        ]:
                    initiate_or_append_list(v, dict, t.number)

                self.zd2zd_dict[t.number] = [t]
                self.zd_dict[t.number] = t

                if (t.rcuk_payment == 'yes') or (t.rcuk_policy == 'yes'):
                    self.zd_dict_RCUK[t.number] = t
                    initiate_or_append_list([t.article_title.upper()], self.title2zd_dict_RCUK, t.number)
                if (t.coaf_payment == 'yes') or (t.coaf_policy == 'yes'):
                    self.zd_dict_COAF[t.number] = t
                    initiate_or_append_list([t.article_title.upper()], self.title2zd_dict_COAF, t.number)
                if t.dup_of not in ['', '-']:
                    self.zd2oa_dups_dict[t.number] = [t.dup_of]

                t.metadata = row

        return [
                self.apollo2zd_dict,
                self.doi2zd_dict,
                self.invoice2zd_dict,
                self.oa2zd_dict,
                self.title2zd_dict,
                self.title2zd_dict_COAF,
                self.title2zd_dict_RCUK,
                self.zd2oa_dups_dict,
                self.zd2zd_dict,
                self.zd_dict,
                self.zd_dict_COAF,
                self.zd_dict_RCUK,
                ]

    def plug_in_payment_data(self, paymentsfile, cufs_export_type='rcuk', funder='rcuk', file_encoding='utf-8'):
        #TODO: Add support for other financial codes that were used in the past for OA charges: VEJE.EDDK.EBKH , GAAB.EBDU
        #TODO: If a OA or ZD number reference is not found in the CUFS report being parsed, try to find a match using invoice number
        '''
        This function parses financial reports produced by CUFS. It tries to mach each payment in the CUFS report
        to a zd ticket and, if successful, it produces summations of payments per zd ticket and appends these
        values to zd_dict as output_apc_field and/or self.cufs_map.total_other

        DEV idea: instead of appending payments to custom fields added to zd_dict, it would probably be better if
        zd_dict was a dictionary of ticket objects indexed by zd_number. We could then use object calculated attributes
        instead of custom fields in a dictionary to store anything useful for reporting and **kwargs for fields
        coming from zendesk

        :param paymentsfile: path of input CSV file containing payment data
        :param cufs_export_type: type of report exported by CUFS. Supported values are 'rcuk' and 'coaf'
        :param funder: 'rcuk' if paymentsfile is a report of a RCUK grant; 'coaf' if it is of a COAF grant
        :param file_encoding: enconding of paymentsfile
        '''

        def calculate_balance(self, payments_dict, zd_number, payments_type):
            '''
            Sums a payment associated with a ZD number to the balance of payments already processed that were also
            associated with that number.

            :param payments_dict:
            :param zd_number:
            :param payments_type:
            :return:
            '''
            if payments_type == 'apc':
                balance_field = self.cufs_map.total_apc
            elif payments_type == 'other':
                balance_field = self.cufs_map.total_other
            existing_payment = payments_dict[zd_number]
            p_amount = float(existing_payment[balance_field].replace(',', ''))
            n_amount = float(row[self.cufs_map.amount_field].replace(',', ''))
            return existing_payment, str(p_amount + n_amount)

        def process_zd_number(self, zd_number):
            logger.debug('--- Working on ZD ticket {}'.format(zd_number))
            if zd_number in cufs.ZD_NUMBER_TYPOS.keys():
                logger.debug('Corrected typo in ZD number; from {} to {}'.format(zd_number,
                                                                                 cufs.ZD_NUMBER_TYPOS[zd_number]))
                zd_number = cufs.ZD_NUMBER_TYPOS[zd_number]

            t = self.zd_dict[zd_number]
            self.zd_dict_with_payments[zd_number] = t

            row_amount = float(row[self.cufs_map.amount_field].replace(',', ''))
            if funder == 'coaf':
                # Payments spreadsheet does not contain transaction field, so assume all payments are APCs
                t.coaf_apc_total += row_amount
                t.apc_grand_total += row_amount
                logger.debug('Funder is COAF. Increased APC amount charged to COAF grant and total APC amount '
                             'by {}; t.coaf_apc_total = {}; t.apc_grand_total = {}'.format(row_amount,
                                                                                           t.coaf_apc_total,
                                                                                           t.apc_grand_total))
            elif funder == 'rcuk':
                if cufs_export_type == 'rcuk':

                    logger.debug('Funder and report format are RCUK. Checking payment codes...')

                    if [row[self.cufs_map.cost_centre],
                        row[self.cufs_map.source_of_funds]] in valid_cc_sof_combos:

                        logger.debug('Checking transaction codes. Row cost centre ({}) and source of funds ({}) '
                                     'codes in list of codes used for publication charges: {}'.format(
                            row[self.cufs_map.cost_centre],
                            row[self.cufs_map.source_of_funds], valid_cc_sof_combos))

                        if row[self.cufs_map.transaction_code] in APC_TRANSACTION_CODES:
                            t.rcuk_apc_total += row_amount
                            t.apc_grand_total += row_amount
                            logger.debug('Row contains APC payment (transaction code {}). Increased APC amount '
                                         'charged to RCUK grant and total APC amount by {}; t.rcuk_apc_total '
                                         '= {}; t.apc_grand_total'
                                         ' = {}'.format(row[self.cufs_map.transaction_code], row_amount,
                                                        t.rcuk_apc_total, t.apc_grand_total))

                        elif row[self.cufs_map.transaction_code] in OTHER_PUB_CHARGES_TRANSACTION_CODES:
                            t.rcuk_other_total += row_amount
                            t.other_grand_total += row_amount
                            logger.debug('Row contains publication charges unrelated to Open Access '
                                         '(transaction code {}). Increased other amount charged to RCUK grant '
                                         'and total other amount by {}; t.rcuk_other_total = {}; t.other_grand_total = '
                                         '{}'.format(row[self.cufs_map.transaction_code],
                                                     row_amount, t.rcuk_other_total, t.other_grand_total))
                        else:
                            # Not a supported transaction code
                            key = 'not_supported_transaction_code_payment_' + str(row_counter)
                            self.rejected_payments[key] = row
                            debug_filename = os.path.join(os.getcwd(),
                                                          nonEBDU_payment_file_prefix + paymentsfile.split('/')[-1])
                            logger.debug('Row transaction code ({}) not supported. '
                                         'Adding row to {}'.format(row[self.cufs_map.transaction_code],
                                                                   debug_filename))
                            output_debug_csv(debug_filename, row, fileheader)

                    else:
                        # Not a supported cost centre/sof combo
                        key = 'not_supported_cc_sof_payment_' + str(row_counter)
                        self.rejected_payments[key] = row
                        debug_filename = os.path.join(os.getcwd(),
                                                      nonJUDB_payment_file_prefix + paymentsfile.split('/')[-1])
                        logger.debug('Adding row to {}. Row cost centre ({}) and source of funds ({}) codes not '
                                     'in list of codes used for publication charges: {}'.format(
                            debug_filename, row[self.cufs_map.cost_centre],
                            row[self.cufs_map.source_of_funds], valid_cc_sof_combos))
                        output_debug_csv(debug_filename, row, fileheader)

                elif cufs_export_type == 'coaf':
                    t.rcuk_apc_total += row_amount
                    t.apc_grand_total += row_amount
                    logger.debug(
                        'Funder is RCUK but CUFS report format is coaf. Increased APC amount charged to RCUK '
                        'grant and total APC amount by {}; t.rcuk_apc_total = {}; t.apc_grand_total = {}'.format(
                            row_amount, t.rcuk_apc_total, t.apc_grand_total))
                # TODO: The elif case for rge export type below is an identical copy of the elif for coaf export type; this should be fine for reports where funder is coaf; for rcuk reports, this might need refinement
                elif cufs_export_type == 'rge':
                    t.rcuk_apc_total += row_amount
                    t.apc_grand_total += row_amount
                    logger.debug(
                        'Funder is RCUK but CUFS report format is rge. Increased APC amount charged to RCUK '
                        'grant and total APC amount by {}; t.rcuk_apc_total = {}; t.apc_grand_total = {}'.format(
                            row_amount, t.rcuk_apc_total, t.apc_grand_total))
                else:
                    sys.exit('{} is not a supported type of financial report (cufs_export_type)'.format(
                        cufs_export_type))
            else:
                sys.exit('{} is not a supported funder'.format(funder))

        if cufs_export_type == 'rcuk':
            self.cufs_map = cufs.RcukFieldsMapping()
        elif cufs_export_type == 'coaf':
            self.cufs_map = cufs.CoafFieldsMapping()
        elif cufs_export_type == 'rge':
            self.cufs_map = cufs.RgeFieldsMapping()
        else:
            sys.exit('{} is not a supported type of financial report (cufs_export_type)'.format(cufs_export_type))

        if funder == 'rcuk':
            self.output_map = cufs.RcukOutputMapping()
        elif funder == 'coaf':
            self.output_map = cufs.CoafOutputMapping()
        else:
            sys.exit('{} is not a supported funder'.format(funder))

        valid_cc_sof_combos = []
        for combo in RCUK_FORMAT_COST_CENTRE_SOF_COMBOS:
            if combo.funder == funder:
                valid_cc_sof_combos.append([combo.cost_centre, combo.sof])
        logger.debug('valid_cc_sof_combos = {}'.format(valid_cc_sof_combos))

        fileheader = extract_csv_header(paymentsfile)

        t_oa = re.compile("OA[ \-]?[0-9]{4,8}")
        t_zd = re.compile("ZD[ \-]{0,3}[0-9]{4,8}")
        t_invoice_number_in_description = re.compile(", inv:([a-zA-Z0-9\-]{4,})")
        payments_dict_apc = {}
        payments_dict_other = {}

        with open(paymentsfile, encoding=file_encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            row_counter = 0
            unmatched_oa_numbers = []
            for row in reader:
                logger.debug('-------------- {} Working on {} row: {}'.format(row_counter, csvfile, row))

                descriptions_of_transactions_processed_manually = []
                if row[self.cufs_map.oa_number] in cufs.AGGREGATED_PAYMENTS.keys():
                    # Transaction aggregating more than one article (e.g. invoice for several articles)
                    # Requires manual break down of charges and addition of description to
                    # descriptions_of_transactions_processed_manually to prevent these aggregated transactions
                    # to be counted more than once
                    if row[self.cufs_map.oa_number] not in descriptions_of_transactions_processed_manually:
                        logger.debug('Aggregated transaction detected ({}). Processing it manually'.format(
                                        row[self.cufs_map.oa_number]))
                        for breakdown in cufs.AGGREGATED_PAYMENTS[row[self.cufs_map.oa_number]]:
                            t = self.zd_dict[breakdown.zd_number]
                            t.rcuk_apc_total = breakdown.rcuk_apc
                            t.coaf_apc_total = breakdown.coaf_apc
                            t.apc_grand_total = t.rcuk_apc_total + t.coaf_apc_total
                            t.rcuk_other_total = breakdown.rcuk_other
                            process_zd_number(self, breakdown.zd_number)
                        descriptions_of_transactions_processed_manually.append(row[self.cufs_map.oa_number])
                    else:
                        logger.debug('Transaction skipped because an aggregated transaction matching this description '
                                    '({}) has already been processed.'.format(self.cufs_map.oa_number))
                    continue    # Do not proceed with normal processing because ZD number of aggregated payment
                                # should not be included in report

                elif row[self.cufs_map.oa_number] in cufs.OA_NUMBER_TYPOS.keys():
                    logger.debug('Corrected typo in OA number; from {} to {}'.format(row[self.cufs_map.oa_number],
                                                        cufs.OA_NUMBER_TYPOS[row[self.cufs_map.oa_number]]))
                    row[self.cufs_map.oa_number] = cufs.OA_NUMBER_TYPOS[row[self.cufs_map.oa_number]]

                m_oa = t_oa.search(row[self.cufs_map.oa_number].upper())
                m_zd = t_zd.search(row[self.cufs_map.oa_number].upper())
                m_invoice_number_in_description = t_invoice_number_in_description.search(row[self.cufs_map.oa_number])
                zd_number = None

                if m_zd:
                    zd_number = m_zd.group().replace(" ","-").strip('ZDzd -')
                    logger.debug('Matched row to ZD number {}'.format(zd_number))

                elif m_oa:
                    oa_number = m_oa.group().upper().replace("OA" , "OA-").replace(" ","").replace('--', '-')
                    logger.debug('Matched row to OA number {}'.format(oa_number))
                    try:
                        zd_number = MANUAL_OA2ZD_DICT[oa_number]
                    except KeyError:
                        try:
                            zd_number_list = self.oa2zd_dict[oa_number]
                            if len(zd_number_list) > 1:
                                logging.error('More than one ZD number is linked to OA number {} {}. Using earliest'
                                              'ZD ticket as match to avoid "TypeError: unhashable type: '
                                              'list". Map OA number manually to ZD number using MANUAL_OA2ZD_DICT to '
                                              'solve this error'.format(oa_number, zd_number_list))
                                zd_number = str(sorted([ int(x) for x in zd_number_list ])[0])
                            else:
                                zd_number = zd_number_list[0]
                        except KeyError:
                            if oa_number not in unmatched_oa_numbers:
                                unmatched_oa_numbers.append(oa_number)
                    if zd_number:
                        logger.debug('Matched row to ZD number {} via OA number {}'.format(zd_number, oa_number))

                elif row[self.cufs_map.invoice_field].strip() in cufs.INVOICE2ZD_NUMBER.keys():
                    # try match by invoice number
                    zd_number = cufs.INVOICE2ZD_NUMBER[row[self.cufs_map.invoice_field]]
                    logger.debug('Matched row to ZD number {} via invoice number {}'.format(zd_number,
                                                                            row[self.cufs_map.invoice_field]))

                elif row[self.cufs_map.oa_number].strip() in cufs.DESCRIPTION2ZD_NUMBER.keys():
                    # try match by description
                    zd_number = cufs.DESCRIPTION2ZD_NUMBER[row[self.cufs_map.oa_number]]
                    logger.debug('Matched row to ZD number {} via description: {}'.format(zd_number,
                                                                                        row[self.cufs_map.oa_number]))

                elif row[self.cufs_map.invoice_field].strip().lower() in self.invoice2zd_dict.keys():
                    zd_number_list = self.invoice2zd_dict[row[self.cufs_map.invoice_field].strip().lower()]
                    if len(zd_number_list) > 1:
                        logger.warning('More than one ZD ticket ({}) matched invoice number {}. Arbitrarily using '
                                       'the first match'.format(zd_number_list,
                                                                row[self.cufs_map.invoice_field].strip()))
                    zd_number = zd_number_list[0]
                    logger.debug('Matched row to ZD number {} via invoice number {} '
                                 'resolved with invoice2zd_dict'.format(zd_number, row[self.cufs_map.invoice_field]))

                elif m_invoice_number_in_description:
                    inv_n = m_invoice_number_in_description.group(1)
                    logger.debug('Invoice number found in description field: {}'.format(inv_n))
                    if inv_n in cufs.INVOICE2ZD_NUMBER.keys():
                        zd_number = cufs.INVOICE2ZD_NUMBER[inv_n]
                        logger.debug('Matched row to ZD number {} via invoice number {} '
                                     'found in description {}'.format(zd_number, inv_n, row[self.cufs_map.oa_number]))
                    elif inv_n.lower() in self.invoice2zd_dict.keys():
                        zd_number_list = self.invoice2zd_dict[inv_n.lower()]
                        if len(zd_number_list) > 1:
                            logger.warning('More than one ZD ticket ({}) matched invoice number {}. Arbitrarily using '
                                       'the first match'.format(zd_number_list, inv_n))
                        zd_number = zd_number_list[0]
                        logger.debug('Matched row to ZD number {} via invoice number {} '
                                 'found in description {} resolved with invoice2zd_dict'.format(zd_number,
                                                                                inv_n, row[self.cufs_map.oa_number]))

                if zd_number:
                    process_zd_number(self, zd_number)
                else:
                    # Payment could not be linked to a zendesk number
                    key = 'no_zd_match_' + str(row_counter)
                    self.rejected_payments[key] = row
                    debug_filename = os.path.join(os.getcwd(), unmatched_payment_file_prefix + paymentsfile.split('/')[-1])
                    logger.debug('Row could not be matched to a ZD number. Adding it to {}'.format(debug_filename))
                    output_debug_csv(debug_filename, row, fileheader)
                row_counter += 1
            if unmatched_oa_numbers:
                unmatched_oa_numbers.sort()
                logger.warning(
                    "ZD numbers could not be found for the following OA numbers in {}: {}. Data for these OA numbers "
                    "will NOT be exported.".format(paymentsfile, unmatched_oa_numbers))

    def plug_in_metadata(self, metadata_file, matching_field, translation_dict, warning_message='', file_encoding='utf-8'):
        '''
        This function appends data from various sources (Apollo, etc) to the dictionaries
        produced from the zendesk export (zd_dict and zd_dict_with_payments)
        :param metadata_file: input CSV file containing data from the new source
        :param matching_field: field to be used to match new data to zd_dict (e.g. doi, title, etc)
        :param translation_dict: dictionary to be used to match new data to a zendesk number
        :param warning_message: message to print if a match could not be found
        :param file_encoding: encoding of input file
        '''
        with open(metadata_file, encoding=file_encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            row_counter = 0
            for row in reader:
                mf = row[matching_field]
                if matching_field in ['doi', 'DOI']:
                    mf = prune_and_cleanup_string(mf, DOI_CLEANUP)
                try:
                    zd_number_list = translation_dict[mf]
                except KeyError:
                    if warning_message:
                        logger.warning(warning_message)
                    zd_number_list = []

                if zd_number_list:
                    for zd in zd_number_list:
                        self.zd_dict[zd].metadata.update(row)
                row_counter += 1