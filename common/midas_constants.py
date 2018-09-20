import collections

from apollo import MetadataMap
from cufs import CoafFieldsMapping, RcukFieldsMapping

RCUK_FUNDER_STR = 'rcuk'
COAF_FUNDER_STR = 'coaf'
ARCADIA_FUNDER_STR = 'arcadia'

class CostCentreAndSofCombo():
    def __init__(self, cost_centre, sof, funder):
        self.cost_centre = cost_centre
        self.sof = sof
        self.funder = funder

RCUK_FORMAT_COST_CENTRE_SOF_COMBOS = [
    CostCentreAndSofCombo('VEJE', 'EDDJ', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJE', 'JUDB', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJE', 'EDDK', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJE', 'GAAA', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJE', 'GAAB', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJF', 'GAAA', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJF', 'JUDB', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJG', 'HANK', ARCADIA_FUNDER_STR),
    CostCentreAndSofCombo('VEJH', 'JUDB', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJI', 'JUDB', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJJ', 'JUDB', RCUK_FUNDER_STR),
    CostCentreAndSofCombo('VEJK', 'JUDB', RCUK_FUNDER_STR),
    ]

COAF_FORMAT_PROJECT_AWARD_COMBOS = [
    CostCentreAndSofCombo('VEAG/044', 'RG80512', COAF_FUNDER_STR),
    CostCentreAndSofCombo('VEAG/045', 'RG82831', COAF_FUNDER_STR),
    CostCentreAndSofCombo('VEAG/050', 'RG88122', COAF_FUNDER_STR),
    CostCentreAndSofCombo('VEAG/052', 'RG93375', COAF_FUNDER_STR),
    CostCentreAndSofCombo('VEAG/054', 'RG96299', RCUK_FUNDER_STR),
    ]

APC_TRANSACTION_CODES = [
    'EBDM',
    'EBDN',
    'EBDU',
    'EBHB',
    'EBKF',
    'EBKG',
    'EBKH',
    'EBKL',
    'EHRB',
    'ERHB',
    'ERHZ',
    'ERJA',
    'EXZZ',
    'EZZM',
    'FKAA',
    'LKAA',
    'LKMB',
    'LKMD',
    'LNBA',
    'VBAK',
]

OTHER_PUB_CHARGES_TRANSACTION_CODES = [
    'EBDV',
    'EBDW',
]


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

ZDFUND2FUNDERSTR = {
    'RCUK payment [flag]' : 'RCUK',
    'COAF payment [flag]' : 'COAF',
    'Other institution payment [flag]' : 'ERROR: OTHER INSTITUTION',
    'Grant payment [flag]' : 'Institutional',
    'Voucher/membership/offset payment [flag]' : 'Institutional',
    'Author/department payment [flag]' : 'Institutional',
    'Wellcome payment [flag]' : 'Wellcome Trust',
    'Wellcome Supplement Payment [flag]' : 'Wellcome Trust',
    'ERC [flag]' : 'ERC',
    'Arthritis Research UK [flag]' : 'Arthritis Research UK',
    'Breast Cancer Now (Breast Cancer Campaign) [flag]' : 'Breast Cancer Campaign',
    "Parkinson's UK [flag]" : "Parkinson's UK",
    'ESRC [flag]' : 'ESRC',
    'NERC [flag]' : 'NERC' ,
    'Bloodwise (Leukaemia & Lymphoma Research) [flag]' : 'Bloodwise',
    'FP7 [flag]' : 'FP7',
    'NIHR [flag]' : 'NIHR',
    'H2020 [flag]' : 'H2020',
    'AHRC [flag]' : 'AHRC',
    'BBSRC [flag]' : 'BBSRC',
    'EPSRC [flag]' : 'EPSRC',
    'MRC [flag]' : 'MRC',
    'Gates Foundation [flag]' : 'Bill and Melinda Gates Foundation',
    'STFC [flag]' : 'STFC',
    'Cancer Research UK [flag]' : 'Cancer Research UK',
    'Wellcome Trust [flag]' : 'Wellcome Trust',
    'British Heart Foundation [flag]': 'British Heart Foundation'
    }

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

JISC_FORMAT_EXPANDED = JISC_FORMAT + ['Id',  # ZD number from zd
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

        from zendesk import ZdFieldsMapping
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
                ('APC paid (£) including VAT if charged', ['ticket.apc_grand_total']), ##CALCULATED FROM 'Amount'
                ('Additional publication costs (£)', ['ticket.other_grand_total']), ##CALCULATED FROM 'Amount'
                #('Discounts, memberships & pre-payment agreements',
                ('Amount of APC charged to COAF grant (including VAT if charged) in £', ['ticket.coaf_apc_total']),
                ('Amount of APC charged to RCUK OA fund (including VAT if charged) in £', ['ticket.rcuk_apc_total']),
                ('Licence', ['EPMC Licence', 'Publisher Licence', zd_map.licence_applied_by_publisher]),
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
















