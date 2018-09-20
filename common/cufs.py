import csv
import logging
import logging.config
import re
import sys

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

###MANUAL FIXES FOR PAYMENT FILES
ZD_NUMBER_TYPOS = {'30878':'50878'}
OA_NUMBER_TYPOS = {'OA 10768':'OA 10468'}
DESCRIPTION2ZD_NUMBER = {
    "OPEN ACCESS FOR R DERVAN'S ARTICLE 'ON K-STABILITY OF FINITE COVERS' IN THE LMS BULLETIN" : '16490',
    'REV CHRG/ACQ TAX PD 04/16;  INV NO:Polymers-123512SUPPLIER:  MDPI AG' : '15589'
}
INVOICE2ZD_NUMBER = {
    ##INPUT FOR RCUK 2017 REPORT
    'APC502145176':'48547',
    'P09819649':'28975',
    'Polymers-123512':'15589',
    'Polymers-123512/BANKCHRG':'15589',
    '9474185' : '18153',
    ##INPUT FOR COAF 2017 REPORT
    '19841M2' : '87254',
    '20170117' : '50542',
    '94189700 BANKCHRG' : '47567'
}
MANUAL_OA2ZD_DICT = {
    'OA-13907':'83033',
    'OA-10518':'36495',
    'OA-13111':'76842',
    'OA-14062':'86232',
    'OA-13919':'83197',
    'OA-14269':'89212'
    }

TOTAL_APC_FIELD = 'Total APC amount'

class CoafFieldsMapping():
    '''
    Mapping of column names in CUFS reports of COAF spending.
    '''
    def __init__(self):
        # self.field_names = extract_csv_header(coaf_paymentsfile, "utf-8")
        self.amount_field = 'Burdened Cost'
        self.invoice_field = 'Invoice'
        self.oa_number =  'Comment'
        self.paydate_field = 'GL Posting Date'
        self.transaction_code = None
        self.source_of_funds = None

class CoafOutputMapping():
    '''
    Mapping of column names for output reports of COAF spending.
    '''
    def __init__(self):
        self.total_apc = 'COAF APC Amount' #Name of field we want the calculated total COAF APC to be stored in
        self.total_other = 'COAF Page, colour or membership amount'  # Name of field we want the total for other costs to be stored in

class RcukFieldsMapping():
    '''
    Mapping of column names in CUFS reports of RCUK spending.
    '''
    def __init__(self):
        # self.field_names = extract_csv_header(rcuk_paymentsfile, "utf-8")
        self.amount_field = 'Amount'
        self.cost_centre = 'CC'
        self.invoice_field = 'Ref 5'
        self.oa_number =  'Description'
        self.paydate_field = 'Posted'
        self.source_of_funds = 'SOF'
        self.transaction_code = 'Tran'

class RcukOutputMapping():
    '''
    Mapping of column names for output reports of RCUK spending.
    '''
    def __init__(self):
        self.total_apc = 'RCUK APC Amount' #Name of field we want the calculated total RCUK APC to be stored in
        self.total_other = 'RCUK Page, colour or membership amount'  # Name of field we want the total for other costs to be stored in