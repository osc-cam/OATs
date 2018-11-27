'''
Parsers for prepayment and offsetting deals
'''

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

class SpringerFieldsMapping():
    '''
    Mapping of column names in Springer reports downloaded from
    https://www.springer.com/gp/myspringer/article-approval-service/reports.
    '''
    def __init__(self):
        self.acceptance_date = 'acceptance date'
        self.amount_paid = None
        self.apc = 'APC'
        self.approval_date = 'approval date'
        self.approval_requested_date = 'approval requested date'
        self.article_title = 'article title'
        self.article_type = 'article type'
        self.currency = 'currency'
        self.discount = None
        self.doi = 'DOI'
        self.doi_url = 'DOI URL'
        self.eissn = 'eISSN'
        self.issn = 'ISSN'
        self.issue_publication_date = 'online issue publication date'
        self.journal = 'journal title'
        self.licence = 'license type'
        self.online_publication_date = 'online first publication date'
        self.request_status = None
        self.transaction_type = None
        self.url = None

        self.report_date = self.approval_date

class WileyFieldsMapping():
    '''
    Mapping of column names in Wiley reports downloaded from the prepayment account dashboard.
    '''
    def __init__(self):
        self.acceptance_date = 'Article Accepted Date'
        self.amount_paid = 'Withdrawals'
        self.apc = 'Full APC'
        self.approval_date = 'Date'
        self.approval_requested_date = None
        self.article_title = 'Article Title'
        self.article_type = 'Article Type'
        self.currency = None
        self.discount = 'Discount'
        self.doi = 'DOI'
        self.doi_url = None
        self.eissn = 'Journal Electronic ISSN'
        self.issn = 'Journal Print ISSN'
        self.issue_publication_date = 'Published in Issue Date'
        self.journal = 'Journal'
        self.licence = 'License Type'
        self.online_publication_date = 'EV Published Date'
        self.request_status = 'Request Status'
        self.transaction_type = None
        self.url = 'Article URL'

        self.report_date = self.approval_date

class OupFieldsMapping():
    '''
    Mapping of column names in OUP reports downloaded from the prepayment account dashboard.
    '''
    def __init__(self):
        self.acceptance_date = 'Editorial Decision Date'
        self.amount_paid = 'Charge Amount'
        self.apc = None
        self.approval_date = 'Order Date'
        self.approval_requested_date = 'Referral Date'
        self.article_title = 'Manuscript Title'
        self.article_type = None
        self.currency = 'Currency'
        self.discount = None
        self.doi = 'Doi'
        self.doi_url = None
        self.eissn = None
        self.issn = None
        self.issue_publication_date = 'Issue Publication'
        self.journal = 'Journal Name'
        self.licence = 'Licence'
        self.online_publication_date = None
        self.request_status = 'Status'
        self.transaction_type = 'Type'
        self.url = None

        self.report_date = self.approval_date

