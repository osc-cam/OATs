'''
Parsers for prepayment and offsetting deals
'''

import csv
import dateutil.parser
import logging
import logging.config

from zenpy import Zenpy

from ..secrets_local import zd_creds, downloads_folder, working_folder
from ..zd_fields_local import ZdFields

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


class ZenClient:
    def __init__(self):
        self.client = Zenpy(**zd_creds)

    def search_for_tickets(self, query):
        return self.client.search(query, type="ticket")


class SpringerFieldsMapping:
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
        self.dateutil_options = dateutil.parser.parserinfo() ## this used to be dateutil.parser.parserinfo(dayfirst=True) for old Springer Compact reports
        self.deposits = None
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


class WileyFieldsMapping:
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
        self.dateutil_options = dateutil.parser.parserinfo(dayfirst=True)
        self.deposits = 'Deposits'
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


class OupFieldsMapping:
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
        self.dateutil_options = dateutil.parser.parserinfo()
        self.deposits = None
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


class PrepaymentReportParser:
    """
        Base parser for reports downloaded from prepayment account dashboards
    """
    def __init__(self, report_filepath, mapping=WileyFieldsMapping(), delim=","):
        self.report_filepath = report_filepath
        self.mapping = mapping
        self.report_rows = []
        with open(self.report_filepath) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delim)
            for row in reader:
                self.report_rows.append(row)

    def prune_rows(self, start_date=None, end_date=None, request_status_field='', dateutil_options=''):
        '''
        This function filters out prepayment records that:
        - were not approved for payment
        - are not an article (some prepayment deals report top ups together with article data)
        - are not within the reporting period

        It returns a tuple, where the first element is an integer (0 for excluded records; 1 for included)
        and the second element is a string specifying the reason for exclusion (if excluded)

        It is not possible to implemented filtering based on values of zendesk fields here
        because this function operates on raw data coming from the prepayment deal; it is
        not linked to zd data yet.

        :param row:
        :param publisher:
        :param filter_date_field:
        :param request_status_field:
        :param dateutil_options:
        :return:
        '''
        filtered_rows = []
        for row in self.report_rows:
            prune = False  # Include records in report by default
            prune_reason = 'BUG: this record was excluded without evaluation by function prune_rows'
            if self.mapping.request_status:
                request_status = row[self.mapping.request_status]
                if request_status in ['Cancelled', 'Rejected', 'Denied', 'Reclaimed']:
                    prune = True
                    prune_reason = 'Rejected request'
            if self.mapping.deposits:
                if not row['Deposits'].strip() == '':
                    prune = True
                    prune_reason = 'Not an article (deposit of funds)'
            #TODO: continue editing this function; ran out of time today!
            if prune and (start_date or end_date):
                approval_date = row[self.mapping.approval_date]
                approval_date = dateutil.parser.parse(approval_date, self.mapping.dateutil_options)
                if start_date <= approval_date <= end_date:
                    prune_reason = ''
                else:
                    prune_reason = 'Out of reporting period'




