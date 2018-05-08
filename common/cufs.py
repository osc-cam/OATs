import logging
import sys

from .oatsutils import extract_csv_header

###MANUAL FIXES FOR PAYMENT FILES
zd_number_typos = {'30878':'50878'}
oa_number_typos = {'OA 10768':'OA 10468'}
description2zd_number = {"OPEN ACCESS FOR R DERVAN'S ARTICLE 'ON K-STABILITY OF FINITE COVERS' IN THE LMS BULLETIN" : '16490', 'REV CHRG/ACQ TAX PD 04/16;  INV NO:Polymers-123512SUPPLIER:  MDPI AG' : '15589'}
invoice2zd_number = {
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

total_apc_field = 'Total APC amount'

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
        self.total_apc = 'COAF APC Amount' #Name of field we want the calculated total COAF APC to be stored in
        self.total_other = 'COAF Page, colour or membership amount'  # Name of field we want the total for other costs to be stored in
        self.transaction_code = None
        self.source_of_funds = None

class RcukFieldsMapping():
    '''
    Mapping of column names in CUFS reports of RCUK spending.
    '''
    def __init__(self):
        # self.field_names = extract_csv_header(rcuk_paymentsfile, "utf-8")
        self.amount_field = 'Amount'
        self.invoice_field = 'Ref 5'
        self.oa_number =  'Description'
        self.paydate_field = 'Posted'
        self.total_apc = 'RCUK APC Amount'  # Name of field we want the calculated total RCUK APC to be stored in
        self.total_other = 'RCUK Page, colour or membership amount'  # Name of field we want the total for other costs to be stored in
        self.transaction_code = 'Tran'
        self.source_of_funds = 'SOF'