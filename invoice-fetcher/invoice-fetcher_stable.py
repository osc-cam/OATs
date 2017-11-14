#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import shutil
import argparse
import re
import time
import subprocess
from pprint import pprint

sys.path.append(os.path.relpath('..'))#this only works if this script is executed from its containing folder.
#sys.path.append(os.path.abspath('/home/asartori/afs_support_files/Scripts/PythonScripts'))
import OATs_common

# parser = argparse.ArgumentParser(description='Fetch invoices from the OSC shared folder based on zendesk ticket matches.')
# parser.add_argument('-p', '--publisher', help='the publisher that issued the invoices of interest')
# parser.add_argument('-t', '--type', help='the type of charges the invoices relate to: APC, page, membership')

def query_zd_dict(case_sensitive=False, **kwargs):
    '''
    This function returns a dictionary containing only zendesk tickets that match ALL
    conditions specified in a query; if the query contains a list of possible values for
    a particular kwarg, then this list will be evaluated on a OR match basis
    :param kwargs: the query
    :return:
    '''
    zd_matches = {}
    for t in zd_dict:
        is_match = True
        for a in kwargs:
            if type(kwargs[a]) == type([0,1]): #if list, match with OR
                subarg_match = False
                for b in kwargs[a]:
                    if case_sensitive==False:
                        if zd_dict[t][a].upper().strip() == b.upper().strip():
                            subarg_match = True
                    elif case_sensitive == True:
                        if zd_dict[t][a].strip() == b.strip():
                            subarg_match = True
                if not subarg_match == True:
                    is_match = False
            else:
                if case_sensitive == False:
                    if not zd_dict[t][a].upper().strip() == kwargs[a].upper().strip():
                        is_match = False
                elif case_sensitive == True:
                    if not zd_dict[t][a].strip() == kwargs[a].strip():
                        is_match = False
        if is_match == True:
            zd_matches[t] = zd_dict[t]
    return(zd_matches)

def copy_invoice_to_current_folder(invoicefolder, oa_number, zd_number, invoice_number, destfolder=os.path.dirname(os.path.realpath(__file__))):
    '''
    This function copies invoices whose filename appear to match data in zendesk from the invoice filing folder
    to the destination folder
    :param invoicefolder: the path to the folder where invoices are filed
    :param oa_number: the OA-number recorded in zendesk
    :param zd_number: the zendesk id of the ticket
    :param invoice_number: the invoice number recorded in zendesk
    :param destfolder: path of the destination folder where the invoice will be copied to
    :return:
    '''
    for i in os.listdir(invoicefolder):
        #matchquality = 0 #'false'
        if (invoice_number in i) and ((oa_number in i) or (zd_number in i)):
         #   matchquality = 10 #'good'
            shutil.copy(os.path.join(invoicefolder, i), destfolder)
            return(True)

# user_query = {'Page/colour invoice processed [flag]':'yes'}
user_query = {'Publisher [txt]':['Royal Society of Chemistry', 'RSC']}

if ('Page/colour invoice processed [flag]' in user_query.keys()) or ('Membership invoice processed [flag]' in user_query.keys()) or ('APC invoice processed [flag]' in user_query.keys()):
    invoicenumberfields = []
    if 'APC invoice processed [flag]' in user_query.keys():
        invoicenumberfields.append('APC invoice number [txt]')
    if 'Membership invoice processed [flag]' in user_query.keys():
        invoicenumberfields.append('Membership invoice number [txt]')
    if 'Page/colour invoice processed [flag]' in user_query.keys():
        invoicenumberfields.append('Page/colour invoice number [txt]')
else:
    invoicenumberfields = ['APC invoice number [txt]', 'Membership invoice number [txt]', 'Page/colour invoice number [txt]']

sharedfolder = 'O:\OSC'
zendeskfolder = os.path.join(sharedfolder, 'DataSources', 'ZendeskExports')
invoicefolder = os.path.join(sharedfolder, 'PaymentsAndCommitments\Invoices\Invoices to be checked')
zendeskexportname = OATs_common.get_latest_csv(zendeskfolder)
zendeskexport = os.path.join(zendeskfolder, zendeskexportname)
# header = OATs_common.extract_csv_header(zendeskexport)
# pprint(header)
(zd_dict, title2zd_dict, doi2zd_dict, oa2zd_dict, apollo2zd_dict, zd2zd_dict) = OATs_common.action_index_zendesk_data_general(zendeskexport)
matches = query_zd_dict(**user_query)
logfilename = 'invoice-fetcher-log.txt'
logfile = open(logfilename, 'w')
for m in matches:
    zdnumber = m
    t = matches[m]
    oanumber = t['externalID [txt]']
    for n in invoicenumberfields:
        invoicenumber = t[n]
        if invoicenumber.strip() not in ['', '-']:
            a = copy_invoice_to_current_folder(invoicefolder, oanumber, zdnumber, invoicenumber)
            if a:
                print('Successfully copied invoice', oanumber, zdnumber, invoicenumber, 'to destination folder')
            else:
                error_message = '''Failed to find invoice for match: OA number: ''' + oanumber + ' ; ZD number: ' + zdnumber + ' ; Invoice number: ' + invoicenumber
                print(error_message)
                logfile.write(error_message + '\n')
                for c in matches[m]:
                    try:
                        logfile.write(c + ' : ' + matches[m][c] + '\n')
                    except UnicodeEncodeError:
                        pass
                logfile.write('\n')
logfile.close()