import collections

from apollo import MetadataMap
from cufs import CoafFieldsMapping, RcukFieldsMapping
from zendesk import ZdFieldsMapping


ZENDESK_EXCLUDED_GROUPS = ['Cron Jobs',
                           'Request a Copy',
                           'Social Media',
                           'Thesis',
                           'Office of Scholarly Communication',
                           'OPs',
                           'Research Data',
                           'Repository'
                           ]

ZENDESK_EXCLUDED_REQUESTERS = ['Dspace',
                               'JIRA Integratrion',
                               'photo',
                               'Accountdashboard',
                               'Cs-onlineopen',
                               'Uptime Robot',
                               'Authorhelpdesk'
                               ]

# declare formats
JISC_FORMAT = ['Date of acceptance',
 'PubMed ID',
 'DOI',
 'Publisher',
 'Journal',
 'E-ISSN',
 'Type of publication',
 'Article title',
 'Date of publication',
 'Fund that APC is paid from (1)',
 'Fund that APC is paid from (2)',
 'Fund that APC is paid from (3)',
 'Funder of research (1)',
 'Grant ID (1)',
 'Funder of research (2)',
 'Grant ID (2)',
 'Funder of research (3)',
 'Grant ID (3)',
 'Date of APC payment',
 'APC paid (actual currency) excluding VAT',
 'Currency of APC',
 'APC paid (£) including VAT if charged',
 'Additional publication costs (£)',
 'Discounts, memberships & pre-payment agreements',
 'Amount of APC charged to COAF grant (including VAT if charged) in £',
 'Amount of APC charged to RCUK OA fund (including VAT if charged) in £',
 'Licence',
 'Notes']

JISC_FORMAT_EXPANDED = JISC_FORMAT + ['id',  # ZD number from zd
                         '#externalID [txt]',  # OA number from zd
                         'Reason for exclusion',  # field calculated and appended by ART
                         # 'Description',             # field from CUFS (RCUK)
                         # 'Ref 1',                   # field from CUFS (RCUK)
                         # 'Ref 5',                   # field from CUFS (RCUK)
                         'Comment',  # field from CUFS (COAF)
                         'Invoice',  # field from CUFS (COAF)
                         'RCUK policy [flag]',  # from zd
                         'RCUK payment [flag]',  # from zd
                         'COAF policy [flag]',  # from zd
                         'COAF payment [flag]',  # from zd
                         'handle'  # from Apollo
                         ]

class ReportTemplate():
    def __init__(self, format=JISC_FORMAT_EXPANDED):

        zd_map = ZdFieldsMapping()
        apollo_map = MetadataMap()
        cufs_rcuk = RcukFieldsMapping()
        cufs_coaf = CoafFieldsMapping()

        self.columns = format
        self.metadata_mapping = collections.OrderedDict(
            [
                ('Date of acceptance', [zd_map.symplectic_acceptance_date_yyyymmdd, 'Acceptance date',
                                        apollo_map.acceptance_date]),
                ('PubMed ID', ['PMID']), #from cottagelabs or Europe PMC map
                ('DOI', [zd_map.doi, apollo_map.doi]),#, 'dc.identifier.uri']), #dc.identifier.uri often contains DOIs that are not in rioxxterms.versionofrecord, but it needs cleaning up (e.g. http://dx.doi.org/10.1111/oik.02622,https://www.repository.cam.ac.uk/handle/1810/254674 ); use only if the DOI cannot be found elsewhere
                ('Publisher', [zd_map.publisher, apollo_map.publisher]),
                ('Journal', [zd_map.journal_title, apollo_map.journal]),
                ('E-ISSN', ['ISSN']), #from cottagelabs
                ('Type of publication', [zd_map.symplectic_item_type, apollo_map.publication_type]),
                ('Article title', [zd_map.manuscript_title, apollo_map.title]),
                ('Date of publication', [zd_map.publication_date, zd_map.online_publication_date_yyyymmdd,
                                         apollo_map.publication_date]),
                ('Date of APC payment', [cufs_rcuk.paydate_field, cufs_coaf.paydate_field]),
                #('APC paid (actual currency) excluding VAT', NA ##COULD PROBABLY OBTAIN FROM CUFS IF REALLY NECESSARY
                #('Currency of APC', NA ##COULD PROBABLY OBTAIN FROM CUFS IF REALLY NECESSARY
                #TODO: total_apc_field was populated by ART by function action_adjust_total_apc_values(), then added to report dict; decide what to do in Midas instead
                ('APC paid (£) including VAT if charged', [total_apc_field]), ##CALCULATED FROM 'Amount'
                ('Additional publication costs (£)', ['Page, colour or membership amount']), ##CALCULATED FROM 'Amount'
                 #('Discounts, memberships & pre-payment agreements',
                ('Amount of APC charged to COAF grant (including VAT if charged) in £', [total_coaf_payamount_field]),
                ('Amount of APC charged to RCUK OA fund (including VAT if charged) in £', [total_rcuk_payamount_field]),
                ('Licence', ['EPMC Licence', 'Publisher Licence', 'Licence applied by publisher [list]'])
                 #('Notes'
            ]
        )
        self.rep_fund_field_list = ['Fund that APC is paid from (1)', 'Fund that APC is paid from (2)',
                               'Fund that APC is paid from (3)']

        self.zd_fund_field_list = ['RCUK payment [flag]', 'COAF payment [flag]', 'Other institution payment [flag]',
                              'Grant payment [flag]', 'Voucher/membership/offset payment [flag]',
                              'Author/department payment [flag]',  # 'Wellcome payment [flag]',
                              'Wellcome Supplement Payment [flag]']

        self.rep_funders = ['Funder of research (1)', 'Funder of research (2)', 'Funder of research (3)']
        self.zd_allfunders = ['Wellcome Trust [flag]',
                         'MRC [flag]',
                         'Cancer Research UK [flag]',
                         'EPSRC [flag]',
                         'British Heart Foundation [flag]',
                         'BBSRC [flag]',
                         'Arthritis Research UK [flag]',
                         'STFC [flag]',
                         "Breast Cancer Now (Breast Cancer Campaign) [flag]",
                         # used to be 'Breast Cancer Campaign [flag]',
                         "Parkinson's UK [flag]",
                         'ESRC [flag]',
                         'Bloodwise (Leukaemia & Lymphoma Research) [flag]',
                         'NERC [flag]',
                         'AHRC [flag]',
                         'ERC [flag]', 'FP7 [flag]', 'NIHR [flag]', 'H2020 [flag]', 'Gates Foundation [flag]',
                         ]

        self.rep_grants = ['Grant ID (1)', 'Grant ID (2)', 'Grant ID (3)']
        self.zd_grantfields = [
            'COAF Grant Numbers [txt]']  # ZD funders field could also be used, but it does not seem to be included in the default export; this could be because it is a "multi-line text field"
















