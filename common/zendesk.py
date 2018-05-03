import csv
import cufs
import datetime
import dateutil.parser
import logging
import sys
from oatsutils import extract_csv_header, output_debug_csv, prune_and_cleanup_string, DOI_CLEANUP, DOI_FIX

### USE THIS DICTIONARY TO FORCE THE MAPPING OF PARTICULARLY PROBLEMATIC OA NUMBERS TO ZD NUMBERS
### FOR EXAMPLE A OA NUMBER MARKED AS DUPLICATE IN ZENDESK, BUT WITH A PAYMENT ASSOCIATED WITH IT
### (SO NOT EASY TO FIX IN ZENDESK)
manual_oa2zd_dict = {
    # 'OA-13907':'83033',
    # 'OA-10518':'36495',
    # 'OA-13111':'76842',
    # 'OA-14062':'86232',
    # 'OA-13919':'83197',
    # 'OA-14269':'89212'
    }

unmatched_payment_file_prefix = 'Midas_debug_payments_not_matched_to_zd_numbers__'
nonJUDB_payment_file_prefix = 'Midas_debug_non_JUDB_payments__'
nonEBDU_payment_file_prefix = 'Midas_debug_non_EBDU_EBDV_or_EBDW_payments__'

class ZdFieldsMapping():
    '''
    A mapping of current Zendesk field names.
    Used to faciliate updating OATs when ZD field names are updated.
    '''
    def __init__(self):
        self.apc_payment = 'Is there an APC payment? [list]'
        self.coaf_payment = 'COAF payment [flag]'
        self.coaf_policy = 'COAF policy [flag]'
        self.doi = 'DOI (like 10.123/abc456) [txt]'
        self.duplicate = 'Duplicate [flag]'
        self.duplicate_of = 'Duplicate of (ZD-123456) [txt]'
        self.embargo = 'Embargo duration [list]'
        self.external_id = 'externalID [txt]'
        self.green_allowed_version = 'Green allowed version [list]'
        self.green_licence = 'Green licence [list]'
        self.id = 'Id'
        self.manuscript_title = 'Manuscript title [txt]'
        self.publication_date = 'Publication date (YYYY-MM-DD) [txt]'
        self.rcuk_payment = 'RCUK payment [flag]'
        self.rcuk_policy = 'RCUK policy [flag]'
        self.repository_link = 'Repository link [txt]'

class Ticket():
    '''
    A single Zendesk ticket
    '''
    def __init__(self):
        '''
        :param self.zd_data: data stored in Zendesk about this ticket
        :param self.rcuk_apc: APC amount charged to RCUK block grant
        :param self.rcuk_other: Amount of other publication fees charged to RCUK block grant
        :param self.decision_score: Integer indicating how likely this ticket is to contain a decision on policies
                and payments
        '''
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
        self.zd_data = {}

class Parser():
    '''
    Parser for Zendesk CSV exports.
    Use this class to read in data exported from Zendesk and parse it into a number of
    dictionaries.
    '''
    def __init__(self):
        self.apollo2zd_dict = {}
        self.cufs_map = None
        self.doi2zd_dict = {}
        self.oa2zd_dict = {}
        self.parsed_payments = {}
        self.grant_report = {}
        self.grant_report_requester = None
        self.grant_report_start_date = None
        self.grant_report_end_date = None
        self.rejected_payments = {}
        self.title2zd_dict = {}
        self.title2zd_dict_COAF = {}
        self.title2zd_dict_RCUK = {}
        self.zd2oa_dups_dict = {}
        self.zd2zd_dict = {}
        self.zd_dict = {}
        self.zd_dict_COAF = {}
        self.zd_dict_RCUK = {}
        self.zd_fields = ZdFieldsMapping()

    def index_zd_data(self, zenexport):
        """ This function parses a csv file exported from the UoC OSC zendesk account
            and returns several dictionaries with the contained data

            :param zenexport: path of the csv file exported from zendesk
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

        def initiate_or_append_list(v, dict, zd_number):
            if v not in ['', '-']:
                if v in dict.keys():
                    dict[v].append(zd_number)
                else:
                    dict[v] = [zd_number]

        with open(zenexport, encoding = "utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
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
                t.apollo_handle = row[self.zd_fields.repository_link].replace('https://www.repository.cam.ac.uk/handle/' , '')
                t.doi = prune_and_cleanup_string(row[self.zd_fields.doi], DOI_CLEANUP, DOI_FIX)
                row[self.zd_fields.doi] = t.doi
                dateutil_options = dateutil.parser.parserinfo(dayfirst=True)
                t.publication_date = convert_date_str_to_yyyy_mm_dd(row[self.zd_fields.publication_date], dateutil_options)
                row[self.zd_fields.publication_date] = t.publication_date
                for v, dict in [
                        (t.apollo_handle, self.apollo2zd_dict),
                        (t.article_title, self.title2zd_dict),
                        (t.doi, self.doi2zd_dict),
                        (t.external_id, self.oa2zd_dict)
                        ]:
                    initiate_or_append_list(v, dict, t.number)

                self.zd2zd_dict[t.number] = t
                self.zd_dict[t.number] = t

                if (t.rcuk_payment == 'yes') or (t.rcuk_policy == 'yes'):
                    self.zd_dict_RCUK[t.number] = t
                    initiate_or_append_list(t.article_title.upper(), self.title2zd_dict_RCUK, t.number)
                if (t.coaf_payment == 'yes') or (t.coaf_policy == 'yes'):
                    self.zd_dict_COAF[t.number] = t
                    initiate_or_append_list(t.article_title.upper(), self.title2zd_dict_COAF, t.number)
                if t.dup_of not in ['', '-']:
                    self.zd2oa_dups_dict[t.number] = t.dup_of

                t.zd_data = row

        return [
                self.apollo2zd_dict,
                self.doi2zd_dict,
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

    def plug_in_payment_data(self, cufs_export_type, paymentsfile, file_encoding = 'utf-8'):
        '''
        This function parses financial reports produced by CUFS. It tries to mach each payment in the CUFS report
        to a zd ticket and, if successful, it produces summations of payments per zd ticket and appends these
        values to zd_dict as output_apc_field and/or self.cufs_map.total_other

        DEV idea: instead of appending payments to custom fields added to zd_dict, it would probably be better if
        zd_dict was a dictionary of ticket objects indexed by zd_number. We could then use object calculated attributes
        instead of custom fields in a dictionary to store anything useful for reporting and **kwargs for fields
        coming from zendesk

        :param cufs_export_type: type of report exported by CUFS. Supported values are 'RCUK' and 'COAF'
        :param paymentsfile: path of input CSV file containing payment data
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

        def parse_apc_payments(self, zd_number, payments_dict_apc, row, row_counter, paymentsfile):
            '''
            Parses APC payments. Used twice by outer function.

            :param self:
            :param zd_number:
            :param payments_dict_apc:
            :param row:
            :param row_counter:
            :param paymentsfile:
            :return:
            '''
            if zd_number in payments_dict_apc.keys():
                # Another APC payment was already recorded for this ticket, so we concatenate values
                existing_payment, balance = calculate_balance(self, payments_dict_apc, zd_number, 'apc')
                for k in row.keys():
                    if (existing_payment[k] != row[k]) and \
                            (k not in [self.cufs_map.paydate_field]):  # DO NOT CONCATENATE PAYMENT DATES
                        n_value = existing_payment[k] + ' %&% ' + row[k]
                    else:
                        n_value = row[k]
                    payments_dict_apc[zd_number][k] = n_value
                payments_dict_apc[zd_number][self.cufs_map.total_apc] = balance
            else:
                payments_dict_apc[zd_number] = row
                payments_dict_apc[zd_number][self.cufs_map.total_apc] = \
                    payments_dict_apc[zd_number][self.cufs_map.amount_field]
            # Now that we dealt with the problem of several apc payments per ticket,
            # add payment info to master dict of zd numbers
            for field in payments_dict_apc[zd_number].keys():
                if (field in self.zd_dict[zd_number].keys()) and (row_counter == 0):
                    logging.warning('Dictionary for ZD ticket {} already contains a field named {}.'
                                    'It will be overwritten by the value in file {}.'.format(zd_number, field,
                                                                                             paymentsfile))
            self.zd_dict[zd_number].update(payments_dict_apc[zd_number])
            return payments_dict_apc

        if cufs_export_type == 'RCUK':
            self.cufs_map = cufs.RcukFieldsMapping()
        elif cufs_export_type == 'COAF':
            self.cufs_map = cufs.CoafFieldsMapping()
        else:
            sys.exit('{} is not a supported type of financial report (cufs_export_type)'.format(cufs_export_type))

        fileheader = extract_csv_header(paymentsfile)

        t_oa = re.compile("OA[ \-]?[0-9]{4,8}")
        t_zd = re.compile("ZD[ \-]?[0-9]{4,8}")
        payments_dict_apc = {}
        payments_dict_other = {}
        with open(paymentsfile, encoding=file_encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            row_counter = 0
            for row in reader:
                if row[self.cufs_map.oa_number] in cufs.oa_number_typos.keys():
                    row[self.cufs_map.oa_number] = cufs.oa_number_typos[row[self.cufs_map.oa_number]]
                m_oa = t_oa.search(row[self.cufs_map.oa_number].upper())
                m_zd = t_zd.search(row[self.cufs_map.oa_number].upper())
                zd_number = None
                if m_oa:
                    oa_number = m_oa.group().upper().replace("OA" , "OA-").replace(" ","")
                    try:
                        zd_number = manual_oa2zd_dict[oa_number] # might be obsolete; test
                    except KeyError:
                        try:
                            zd_number = self.oa2zd_dict[oa_number]
                        except KeyError:
                            logging.warning('A ZD number could not be found for {} in {}.' 
                                            'Data for this OA number will be ignored'.format(oa_number, paymentsfile))
                elif m_zd:
                    zd_number = m_zd.group().replace(" ","-").strip('ZDzd -')

                if row[self.cufs_map.invoice_field].strip() in cufs.invoice2zd_number.keys():
                    zd_number = cufs.invoice2zd_number[row[self.cufs_map.invoice_field]]

                if row[self.cufs_map.oa_number].strip() in cufs.description2zd_number.keys():
                    zd_number = cufs.description2zd_number[row[self.cufs_map.oa_number]]

                if zd_number:
                    if zd_number in cufs.zd_number_typos.keys():
                        zd_number = cufs.zd_number_typos[zd_number]

                    t = self.zd_dict[zd_number]

                    if cufs_export_type == 'COAF':
                        # Payments spreadsheet does not contain transaction field, so assume all payments are APCs
                        t.coaf_apc_total += row[self.cufs_map.amount_field]
                    elif cufs_export_type == 'RCUK':
                        if row[self.cufs_map.transaction_code] == 'EBDU':
                            t.rcuk_apc_total += row[self.cufs_map.amount_field]
                        elif row[self.cufs_map.transaction_code] in ['EBDV', 'EBDW']:
                            t.rcuk_other_total += row[self.cufs_map.amount_field]
                        else:
                            # Not a EBDU, EBDV or EBDW payment
                            key = 'not_EBD*_payment_' + str(row_counter)
                            self.rejected_payments[key] = row
                            debug_filename = os.path.join(os.getcwd(),
                                                          nonEBDU_payment_file_prefix + paymentsfile.split('/')[-1])
                            output_debug_csv(debug_filename, row, fileheader)
                    else:
                        sys.exit('{} is not a supported type of financial report (cufs_export_type)'.format(cufs_export_type))
                else:
                    # Payment could not be linked to a zendesk number
                    key = 'no_zd_match_' + str(row_counter)
                    self.rejected_payments[key] = row
                    debug_filename = os.path.join(os.getcwd(), unmatched_payment_file_prefix + paymentsfile.split('/')[-1])
                    output_debug_csv(debug_filename, row, fileheader)
                row_counter += 1

    def plug_in_metadata(self, metadata_file, matching_field, translation_dict, warning_message='', file_encoding='utf-8'):
        '''
        This function appends data from various sources (Apollo, etc) to the main dictionary
        produced from the zendesk export (self.zd_dict)
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
                zd_number_list = []
                try:
                    zd_number_list = translation_dict[mf]
                except KeyError:
                    if warning_message:
                        print(warning_message)

                if zd_number_list:
                    for zd_number in zd_number_list:
                        if row_counter < 4:
                            for field in row.keys():
                                if field in zd_dict[zd_number].keys():
                                    logging.warning('Dictionary for ZD ticket {} already contains a field named {}.' 
                                        'It will be overwritten by the value in file {}'.format(zd_number, field ,
                                                                                                metadata_file))
                        zd_dict[zd_number].update(row)
                row_counter += 1

    def populate_grant_report(self):
        '''
        This function iterates through self.zd_dict after it has received data from all input sources.
        It then selects tickets that will be included in the report, based on the following criteria:
        -

        I THINK THIS FUNCTION IS NOT DOING WHAT IT SHOULD BE DOING FOR COAF PAYMENTS; FIX IT

        ADD SUPPORT FOR REPORTS COMBINING ALL PAYMENTS BY RCUK AND COAF

        :return:
        '''

        paydate_field = self.cufs_map.paydate_field

        if self.grant_report_requester == 'RCUK':
            datetime_format_st = '%d-%b-%Y'  # e.g 21-APR-2016
        elif self.grant_report_requester == 'COAF':
            datetime_format_st = '%d-%b-%y'  # e.g 21-APR-16
        else:
            sys.exit('ERROR: unrecognised grant report requester: {}'.format(self.grant_report_requester))

        zd_dict_counter = 0
        for a in self.zd_dict:
            ## CHECK IF THERE IS A PAYMENT FROM REPORT REQUESTER;
            ## IF THERE IS, ADD TO self.grant_report (I.E. INCLUDE IN REPORT)
            try:
                payments = self.zd_dict[a][paydate_field].split('%&%')
                for p in payments:
                    ### QUICK AND DIRTY FIX FOR COAF REPORT; ALMOST CERTAINLY BREAKS RCUK REPORT GENERATION
                    self.grant_report[a] = self.zd_dict[a]
                    ### END OF QUICK AND DIRTY FIX FOR COAF REPORT
                    payment_date = datetime.datetime.strptime(p.strip(), datetime_format_st)
                    if self.grant_report_start_date <= payment_date <= self.grant_report_end_date:
                        self.grant_report[a] = self.zd_dict[a]
                    else:
                        key = 'out_of_reporting_period_' + str(zd_dict_counter)
                        self.rejected_payments[key] = self.zd_dict[a]
            except KeyError:
                pass
                ## THIS WARNING IS NOT A GOOD IDEA BECAUSE MANY TICKETS OLDER THAN THE REPORTING PERIOD MATCH THIS CONDITION
                # ~ if zd_dict[a]['RCUK payment [flag]'] == 'yes':
                # ~ print('WARNING: RCUK payment ticked in zendesk but no RCUK payment located for record:')
                # ~ pprint(zd_dict[a])
                # ~ print('\n')
            zd_dict_counter += 1