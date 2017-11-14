#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import shutil
import argparse
import re
import csv
from pprint import pprint

sys.path.append(os.path.relpath('..'))#this only works if this script is executed from its containing folder.
#sys.path.append(os.path.abspath('/home/asartori/afs_support_files/Scripts/PythonScripts'))
import OATs_common

# parser = argparse.ArgumentParser(description='Fetch invoices from the OSC shared folder based on zendesk ticket matches.')
# parser.add_argument('-p', '--publisher', help='the publisher that issued the invoices of interest')
# parser.add_argument('-t', '--type', help='the type of charges the invoices relate to: APC, page, membership')

def plog(*args):
    '''
    Function to print arguments to global log file. Use for debugging purposes.
    Otherwise, define it as pass
    :param args: Arguments to print to log
    '''
    # #with open(logfilename, 'a') as logfile:
    # for a in args:
    #     a = str(a)
    #     logfile.write(a + ' ')
    # logfile.write('\n')
    pass

def query_zd_dict(case_sensitive=False, match_all=True, **kwargs):
    '''
    This function returns a dictionary containing only zendesk tickets that match ANY or ALL
    conditions specified in a query (depending on the value of parameter match_all);
    if the query contains a list of possible values for a particular kwarg,
    then this list will be evaluated on a OR match basis
    :param kwargs: the query
    :return:
    '''
    zd_matches = {}
    if match_all == True:
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
    elif match_all == False:
        for t in zd_dict:
            is_match = False
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
                    if subarg_match == True:
                        is_match = True
                else:
                    if case_sensitive == False:
                        if zd_dict[t][a].upper().strip() == kwargs[a].upper().strip():
                            is_match = True
                    elif case_sensitive == True:
                        if zd_dict[t][a].strip() == kwargs[a].strip():
                            is_match = True
            if is_match == True:
                zd_matches[t] = zd_dict[t]
    else:
        print('query_zd_dict: ERROR: match_all can only be True or False.')
    return(zd_matches)

###MANUAL FIXES FOR PAYMENT FILES
zd_number_typos = {} #{'30878':'50878'}
oa_number_typos = {} #{'OA 10768':'OA 10468'}
invoice2zd_number = {'APC502145176':'48547', 'P09819649':'28975', 'Polymers-123512':'15589', 'Polymers-123512/BANKCHRG'
    :'15589', '9474185' : '18153'}
description2zd_number = {"OPEN ACCESS FOR R DERVAN'S ARTICLE 'ON K-STABILITY OF FINITE COVERS' IN THE LMS BULLETIN" : '16490', 'REV CHRG/ACQ TAX PD 04/16;  INV NO:Polymers-123512SUPPLIER:  MDPI AG' : '15589'}

def get_invoice_variables_from_finance_report(paymentsfile, oa_number_field, invoice_field='Ref 5', file_encoding='utf-8',
                         transaction_code_field='Tran', source_funds_code_field='SOF'):
    '''
    This function parses financial reports produced by CUFS and returns a list of invoice variables
    :param paymentsfile: path of input CSV file containing payment data
    :param oa_number_field: name of field in input file containing "OA-" numbers
    :param invoice_field: name of field in input file containing invoice numbers
    :param file_encoding: enconding of input file
    :param transaction_code_field: name of field in input file containing the transaction code
                                    for APC payments (EBDU) or page/colour (EBDV)
    :param source_funds_code_field: name of field in input file containing the source of funds code (JUDB)
    '''
    t_oa = re.compile("OA[ \-]?[0-9]{4,8}")
    t_zd = re.compile("ZD[ \-]?[0-9]{4,8}")
    invoicevariables = []
    with open(paymentsfile, encoding=file_encoding) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            invoice_number =  row[invoice_field].strip()
            source_funds_code = row[source_funds_code_field].strip() #'JUDB'
            transaction_code = row[transaction_code_field].strip() #'EBDU'
            oa_number = ''
            if row[oa_number_field] in oa_number_typos.keys():
                row[oa_number_field] = oa_number_typos[row[oa_number_field]]
            # print('\n', 'oa_number_field:', oa_number_field)
            m_oa = t_oa.search(row[oa_number_field].upper())
            m_zd = t_zd.search(row[oa_number_field].upper())
            # before = row[oa_number_field]
            if m_oa:
                oa_number = m_oa.group().upper().replace("OA", "OA-").replace(" ", "").replace('--','-')
                try:
                    zd_number = oa2zd_dict[oa_number]
                except KeyError:
                    ### MANUAL FIX FOR OLD TICKET
                    if oa_number == "OA-1128":
                        zd_number = '3743'  # DOI: 10.1088/0953-2048/27/8/082001
                    else:
                        print("WARNING: A ZD number could not be found for", oa_number, "in",
                              paymentsfile + ". Data for this OA number will NOT be exported.")
                        zd_number = ''
            elif m_zd:
                zd_number = m_zd.group().replace(" ", "-").strip('ZDzd -')
            else:
                zd_number = ''
            if invoice_number in invoice2zd_number.keys():
                zd_number = invoice2zd_number[row[invoice_field]]
            if row[oa_number_field].strip() in description2zd_number.keys():
                zd_number = description2zd_number[row[oa_number_field]]
            if zd_number:
                if zd_number in zd_number_typos.keys():
                    zd_number = zd_number_typos[zd_number]
            invoicevariables.append((invoice_number, source_funds_code, transaction_code, oa_number, zd_number))
    return(invoicevariables)

def copy_invoice_to_current_folder(invoicefolder, oa_number, zd_number, invoice_number, destfolder=os.path.dirname(os.path.realpath(__file__)), case_sensitive=False):
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
    invoice_number = invoice_number.strip()
    oa_number = oa_number.strip()
    zd_number = zd_number.strip()
    dubiousfolder = os.path.join(destfolder, 'matches_on_invoice_number_alone')
    status = False
    matchquality = 0  # 'false'
    if not os.path.exists(dubiousfolder):
        os.makedirs(dubiousfolder)
    # for i in os.listdir(invoicefolder):
    #     status = False
    #     if (invoice_number in i) and ((oa_number in i) or (zd_number in i)):
    #         status = True
    #         matchquality = 10  # 'good'
    #         shutil.copy2(os.path.join(invoicefolder, i), destfolder)
    #     elif invoice_number in i:
    #         status = True
    #         matchquality = 5  # 'satisfactory'
    #         shutil.copy2(os.path.join(invoicefolder, i), dubiousfolder)
    #     else:
    #         matchquality = 0  # 'false'
    #     return (status, matchquality)
    for root, dirs, files in os.walk(invoicefolder, topdown=False):
        plog('ROOT:', root)
        for i in files:
            plog(i)
            plog(invoice_number, oa_number, zd_number)
            if case_sensitive == False:
                i = i.upper()
                invoice_number = invoice_number.upper()
                oa_number = oa_number.upper()
                zd_number = zd_number.upper()
            if (invoice_number in i) and ((oa_number != '') or (zd_number != '')) and ((oa_number in i) or (zd_number in i)):
                plog('Good match!')
                status = True
                matchquality = 10 #'good'
                shutil.copy2(os.path.join(root, i), destfolder)
            elif invoice_number in i:
                plog('Satisfactory match!')
                status = True
                matchquality = 5  # 'satisfactory'
                shutil.copy2(os.path.join(root, i), dubiousfolder)
            else:
                plog('No match!')
    plog(status, matchquality)
    return (status, matchquality)

def search_using_cufs_data(*args):
    '''
    Takes a tuple of the CUFS reports and searches each of them for invoices matching the global
    variable user_query
    :param args: tuple listing CUFS reports to be included in the search
    '''
    logfile = open(logfilename, 'a')
    logfile.write('Began search for invoices using CUFS data')
    queries = list(user_query.keys())
    for invoice_type in ['Page/colour invoice processed [flag]', 'Membership invoice processed [flag]', 'APC invoice processed [flag]']:
        try:
            queries.remove(invoice_type)
        except ValueError:
            pass
    if len(queries) > 0:
        query_zd_data = True
    else:
        query_zd_data = False
    for report in args:
        print('Parsing finance report:', report)
        plog('Parsing finance report:', report)
        invoices = get_invoice_variables_from_finance_report(os.path.join(financereportsfolder, report), 'Description')
        for i in invoices:
            (invoicenumber, source_funds_code, transaction_code, oanumber, zdnumber) = i
            # print(invoicenumber, source_funds_code, transaction_code, oanumber, zdnumber)
            if (query_zd_data == False) or ((query_zd_data == True) and (zdnumber in matches.keys())):
                for code in target_transaction_codes:
                    if code.upper() == transaction_code.upper():

                        if invoicenumber.strip() not in ['', '-']:
                            print(invoicenumber, source_funds_code, transaction_code, oanumber, zdnumber)
                            plog(invoicenumber, source_funds_code, transaction_code, oanumber, zdnumber)
                            (a, quality) = copy_invoice_to_current_folder(invoicefolder, oanumber, zdnumber, invoicenumber)
                            if a and (quality == 10):
                                print('Successfully copied invoice', oanumber, zdnumber, invoicenumber,
                                      'to destination folder')
                            elif a and (quality == 5):
                                print('Successfully copied invoice', oanumber, zdnumber, invoicenumber,
                                      'to destination folder based on invoice number alone')
                            elif a:
                                print('Successfully copied invoice', oanumber, zdnumber, invoicenumber,
                                      'WITH UNKNOWN QUALITY OR DESTINATION')
                            else:
                                error_message = '''Failed to find invoice for OA number: ''' + oanumber + ' ; ZD number: ' + zdnumber + ' ; Invoice number: ' + invoicenumber
                                print(error_message)
                                logfile.write(error_message + '\n')
    logfile.write('Ended search for invoices using CUFS data')
    logfile.close()

def search_using_zendesk_data(user_query):
    '''
    Takes a dictionary containing one or more queries of the kind {zendesk field : value}. For Zendesk tickets matching
    all queried fields, it then checks if there is an invoice associated with them and, if so, copies those invoices
    to working directory
    :param user_query: dictionary containing one or more queries of the kind {zendesk field : value}
    '''
    logfile = open(logfilename, 'a')
    logfile.write('Began search for invoices using Zendesk data')
    for m in matches:
        zdnumber = m
        t = matches[m]
        oanumber = t['externalID [txt]']
        for n in invoicenumberfields:
            invoicenumber = t[n]
            if invoicenumber.strip() not in ['', '-']:
                a, quality = copy_invoice_to_current_folder(invoicefolder, oanumber, zdnumber, invoicenumber)
                if a and (quality == 10):
                    print('Successfully copied invoice', oanumber, zdnumber, invoicenumber, 'to destination folder')
                elif a and (quality == 5):
                    print('Successfully copied invoice', oanumber, zdnumber, invoicenumber,
                          'to destination folder based on invoice number alone')
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
    logfile.write('Ended search for invoices using Zendesk data')
    logfile.close()

# user_query = {'Page/colour invoice processed [flag]':'yes'}
#user_query = {'Publisher [txt]':['Royal Society of Chemistry', 'RSC']}
user_query = {'Corresponding author [txt]':['Prof Paul Lehner', 'Paul J Lehner (CIMR)', 'Paul J. Lehner', 'Paul J Lehner',
                                            'Paul Lehner', 'Nicholas Matheson and Paul Lehner', 'Professor Paul Lehner',
                                            'Edward Greenwood and Paul Lehner', 'Prof. Paul Lehner'],
            'Requester id':'880600338'}
search_method = 'both'  # allowed values are 'zendesk', 'cufs' or 'both'
                        # method cufs expects one or more csv files of cufs reports
                        # of the type 'Account Analysis - Transaction Detail - Excel Version (UFS)'
match_method = 'any'    # allowed values are 'any' or 'all'
                        # 'any' will return invoices matching any conditions specified in user_query
                        # 'all' will return only invoices matching all conditions specified in user_query
print('user_query:', user_query)
print('search_method:', search_method)
print('match_method:', match_method)

if ('Page/colour invoice processed [flag]' in user_query.keys()) or ('Membership invoice processed [flag]' in user_query.keys()) or ('APC invoice processed [flag]' in user_query.keys()):
    invoicenumberfields = []
    target_transaction_codes = []
    if 'APC invoice processed [flag]' in user_query.keys():
        invoicenumberfields.append('APC invoice number [txt]')
        target_transaction_codes.append('EBDU')
    if 'Membership invoice processed [flag]' in user_query.keys():
        invoicenumberfields.append('Membership invoice number [txt]')
        target_transaction_codes.append('EBDV')
    if 'Page/colour invoice processed [flag]' in user_query.keys():
        invoicenumberfields.append('Page/colour invoice number [txt]')
        target_transaction_codes.append('EBDW')
else:
    invoicenumberfields = ['APC invoice number [txt]', 'Membership invoice number [txt]', 'Page/colour invoice number [txt]']
    target_transaction_codes = ['EBDU', 'EBDV', 'EBDW']

# print(invoicenumberfields)
# print(target_transaction_codes)


sharedfolder = 'O:\OSC'
datasourcesfolder = os.path.join(sharedfolder, 'DataSources')
zendeskfolder = os.path.join(datasourcesfolder, 'ZendeskExports')
financereportsfolder = os.path.join(datasourcesfolder, 'FinanceReports')
invoicefolder = os.path.join(sharedfolder, 'PaymentsAndCommitments\Invoices')
#invoicefolder = os.path.join(sharedfolder, 'PaymentsAndCommitments\Invoices\Invoices to be checked')
zendeskexportname = OATs_common.get_latest_csv(zendeskfolder)
zendeskexport = os.path.join(zendeskfolder, zendeskexportname)
# header = OATs_common.extract_csv_header(zendeskexport)
# pprint(header)
print('parsing data exported from zendesk into zd_dict')
(zd_dict, title2zd_dict, doi2zd_dict, oa2zd_dict, apollo2zd_dict, zd2zd_dict) = OATs_common.action_index_zendesk_data_general(zendeskexport)

matches = query_zd_dict(**user_query)
logfilename = 'invoice-fetcher-log.txt'
logfile = open(logfilename, 'w')
logfile.close()

if search_method in ['cufs']:
    search_using_cufs_data('VEJE TRX REPORT JAN 12 - MAR 17.csv', 'VEJH TRX REPORT JAN 12 - MAR 17.csv',
     'VEJI TRX REPORT JAN 12 - MAR 17.csv')
elif search_method in ['zendesk']:
    search_using_zendesk_data(user_query)
elif search_method in ['both']:
    search_using_cufs_data('VEJE TRX REPORT JAN 12 - MAR 17.csv', 'VEJH TRX REPORT JAN 12 - MAR 17.csv',
                           'VEJI TRX REPORT JAN 12 - MAR 17.csv')
    search_using_zendesk_data(user_query)
else:
    print('ERROR: Search method', search_method, 'unknown!')