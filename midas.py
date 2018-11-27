#!/usr/bin/env python3

## Ideas
# - arguments for reporting period, type of report to generate

__version__ = '2018.04'
__author__ = 'André Sartori'

import argparse
import os
import re
import csv
import datetime
import dateutil.parser
import collections
import logging
import logging.config
import sys
import xlsxwriter
from pprint import pprint
from difflib import SequenceMatcher

import common.cufs as cufs
import common.midas_constants as mc
import common.zendesk as zendesk
from common.oatsutils import convert_date_str_to_yyyy_mm_dd, extract_csv_header, get_latest_csv, output_debug_csv

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

class Article():
    '''
    Each article in the output report
    '''


class Report():
    '''
    The report object
    '''

    def __init__(self, zenexport, report_type='all', fieldnames=mc.JISC_FORMAT_EXPANDED,
                 period_start=datetime.datetime(2000, 1, 1), period_end=datetime.datetime.now().date()):
        self.period_start = period_start
        self.period_end = period_end
        if report_type == 'all':
            self.rcuk = True
            self.coaf = True
        elif report_type == 'rcuk':
            self.rcuk = True
            self.coaf = False
        elif report_type == 'coaf':
            self.rcuk = False
            self.coaf = True

        # include/exclude from report (include everything by default)
        self.invoices = True
        self.springer = True
        self.wiley = True
        self.oup = True
        self.frontiers = True

        # include/exclude metadata to be combined with ZD export (include everything by default)
        self.apollo = True
        self.pmc = True

        self.zd_parser = zendesk.Parser(zenexport)

        self.fieldnames = fieldnames
        self.articles=[]

    def output_csv(self):
        filename = '{}_midas_report.csv'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames, extrasaction='ignore')
            writer.writeheader()
            for a in self.articles:
                ticket = a.metadata
                exclude = 0
                # for field, value in exclusion_list:
                #     # print('\n')
                #     # print(report_dict[ticket].keys())
                #     # print('APC:', zd_dict[a][field])
                #     # print(value)
                #     if (field in report_dict[ticket].keys()) and (str(report_dict[ticket][field]).strip() == value):
                #         #   print('excluded')
                #         exclude = 1
                # # print(report_dict[ticket])
                if exclude == 0:
                    writer.writerow(ticket)
                # else:
                #     excluded_recs[ticket] = report_dict[ticket]

    def parse_cufs_data(self, cufs_datasources=None):
        '''
        Populates self.zd_parser.zd_dict with data from CUFS reports. Once all CUFS reports have been parsed,
        add zendesk.Ticket.apc_grand_total and other total amount fields as kwargs to self.zd_parser.zd_dict and
        self.zd_parser.zd_dict_with_payments   

        :param cufs_datasources: An array of CUFS reports, each being a list in the format [filename, format, funder]
        '''

        if not self.zd_parser.zd_dict.keys():
            self.zd_parser.index_zd_data()
        for datasource in cufs_datasources:
            logger.info('Parsing CUFS report {}'.format(datasource))
            self.zd_parser.plug_in_payment_data(datasource[0], datasource[1], datasource[2])

        for dict in [self.zd_parser.zd_dict, self.zd_parser.zd_dict_with_payments]:
            for k, t in dict.items():
                if t.apc_grand_total or t.other_grand_total:
                    t.metadata['ticket.apc_grand_total'] = str(t.apc_grand_total)
                    t.metadata['ticket.other_grand_total'] = str(t.other_grand_total)
                    t.metadata['ticket.coaf_apc_total'] = str(t.coaf_apc_total)
                    t.metadata['ticket.coaf_other_total'] = str(t.coaf_other_total)
                    t.metadata['ticket.rcuk_apc_total'] = str(t.rcuk_apc_total)
                    t.metadata['ticket.rcuk_other_total'] = str(t.rcuk_other_total)

    def plugin_apollo(self, apollo_exports=None):
        '''
        Populates self.zd_parser.zd_dict with data from Apollo reports

        :param apollo_exports: A list of Apollo reports
        '''
        if not self.zd_parser.zd_dict.keys():
            self.zd_parser.index_zd_data()
        for datasource in apollo_exports:
            logger.info('Parsing Apollo export {}'.format(datasource))
            self.zd_parser.plug_in_metadata(datasource, 'handle', self.zd_parser.apollo2zd_dict)

    def parse_old_payments_spreadsheet(self, csv_path=None):
        #TODO: This function can probably be deleted. Pluging in data from this old spreadsheet is probably the wrong way to go about this. It is probably better to use this old sheet only to try to identify CUFS transactions that could not be easily linked to ZD
        '''
        Populates self.zd_parser.zd_dict with data from the main sheet of the spreadsheet of payments
        (LST_AllFinancialData_V3_20160721_Main_Sheet.csv) maintained by the OA Team
        to record payments of Open Access tickets received before 01/01/2016 (before all payment data began to
        be recorded in Zendesk)
        '''
        if not self.zd_parser.zd_dict.keys():
            self.zd_parser.index_zd_data()
        if not csv_path:
            try:
                csv_path = os.path.join('~', 'OSC-shared-drive', 'OSC', 'DataSources', 'FinanceReports',
                                        'LST_AllFinancialData_V3_20160721_Main_Sheet.csv')
            except Exception as e:
                sys.exit('{}; {}'.format(e, e.args))

        logger.info('Parsing old payment spreadsheet {}'.format(csv_path))
        self.zd_parser.plug_in_metadata(csv_path, 'Zendesk Number', self.zd_parser.zd2zd_dict)

    def plugin_pmc(self, pmc_exports=None):
        '''
        Populates self.zd_parser.zd_dict with data from Europe PMC
        :param pmc_exports: A list of PMC exports
        '''
        if not self.zd_parser.zd_dict.keys():
            self.zd_parser.index_zd_data()
        for datasource in pmc_exports:
            logger.info('Parsing EuropePMC export {}'.format(datasource))
            self.zd_parser.plug_in_metadata(datasource, 'DOI', self.zd_parser.doi2zd_dict)

    def populate_invoiced_articles(self, debug_csv='Midas_debug_tickets_without_payments_from_report_requester_or_a_'
                                                   'balance_of_zero.csv'):
        '''
        Iterates through self.zd_parser.zd_dict_with_payments and populates self.articles with zendesk.Ticket objects
        containg payments
        '''
        for k, t in self.zd_parser.zd_dict_with_payments.items():
            if self.rcuk and (t.rcuk_apc_total or t.rcuk_other_total):
                self.articles.append(t)
                logger.debug('ZD number {} contains RCUK payments. Adding ticket to Report.articles'.format(k))
            elif self.coaf and (t.coaf_apc_total or t.coaf_other_total):
                self.articles.append(t)
                logger.debug('ZD number {} contains COAF payments. Adding ticket to Report.articles'.format(k))
            else:
                logger.debug('Adding ZD ticket info to {}. ZD number {} either does not contain payments from report requester '
                             '(e.g. RCUK and/or COAF) or the balance of payments is zero. It will '
                             'not be included in Report.articles'.format(debug_csv, k))
                t.output_payment_summary_as_csv(os.path.join(working_folder, debug_csv))

    def populate_report_fields(self, report_template, default_publisher='', default_pubtype='',
                                      default_deal='', default_notes=''):
        '''
        This function iterates through self.articles and populates in self.articles.metadata the data fields that
        will be used in the output report

        :param translation_dict: an instance of midas_constants.ReportTemplate, containing a dictionary mapping
                    report fields to data source fields
        :param default_publisher: used for prepayment deals; if set, publisher will be set to this value
        :param default_pubtype: used for prepayment deals; if set, pubtype will be set to this value
        :param default_deal: used for prepayment deals; if set, deal will be set to this value
        :param default_notes: used for prepayment deals; if set, notes will be set to this value
        '''

        def process_repeated_fields(zd_list, report_field_list, ticket):
            '''
            This function populates fields in the output report that do NOT have a 1 to 1
            correspondence to zendesk data fields (e.g. Fund that APC is paid from (1)(2) and (3))
            :param dict: the reporting dictionary
            :param zd_list: list of zendesk data fields that may be used to populate the output fields
            :param report_field_list: list of output report fields that should be populated with data from
                                        fields in zd_list
            :param ticket: dictionary representation of ZD ticket to work on
            :return:
            '''
            used_funders = []
            for fund_f in report_field_list:  # e.g. Fund that APC is paid from (1)(2) and (3)
                for zd_f in zd_list:  # 'RCUK payment [flag]', 'COAF payment [flag]', etc
                    if (fund_f not in ticket.keys()) and (zd_f not in used_funders):
                        ## 'Fund that APC is paid from 1, 2 or 3' NOT YET SET FOR THIS TICKET
                        if '[flag]' in zd_f:
                            if ticket[zd_f].strip().upper() == 'YES':
                                # print('zdfund2funderstr[zd_f]:', zdfund2funderstr[zd_f])
                                ticket[fund_f] = mc.ZDFUND2FUNDERSTR[zd_f]
                                used_funders.append(zd_f)
                        else:
                            if not ticket[zd_f].strip() == '-':
                                # print(ticket[zd_f]:', ticket[zd_f])
                                ticket[fund_f] = ticket[zd_f]
                                used_funders.append(zd_f)
            return ticket

        translation_dict = report_template.metadata_mapping

        for a in self.articles:
            ticket = a.metadata
            for rep_f in translation_dict:
                for zd_f in translation_dict[rep_f]:
                    if zd_f in ticket.keys():
                        if ticket[zd_f]:  # avoids AttributeError due to NoneType objects
                            if not ticket[zd_f].strip() in ['-', 'unknown']:  # ZD uses "-" to indicate NA #cottagelabs uses "unknown" to indicate NA for licence
                                # convert dates to YYYY-MM-DD format
                                if (rep_f in ['Date of APC payment', 'Date of publication']) and (
                                    default_publisher == 'Wiley'):
                                    ticket[zd_f] = convert_date_str_to_yyyy_mm_dd(ticket[zd_f])
                                ticket[rep_f] = ticket[zd_f]
                                # ticket[rep_f] = ticket[zd_f] + ' | ' + zd_f ##USE THIS IF YOU NEED TO FIND OUT WHERE EACH BIT OF INFO IS COMING FROM
            ##THEN WITH THE CONDITIONAL FIELDS
            ticket = process_repeated_fields(report_template.zd_fund_field_list, report_template.rep_fund_field_list,
                                             ticket)
            ticket = process_repeated_fields(report_template.zd_allfunders, report_template.rep_funders, ticket)
            ticket = process_repeated_fields(report_template.zd_grantfields, report_template.rep_grants, ticket)

            if default_publisher:
                ticket['Publisher'] = default_publisher
            if default_pubtype:
                ticket['Type of publication'] = default_pubtype
            if default_deal:
                ticket['Discounts, memberships & pre-payment agreements'] = default_deal
            # add GBP as currency for Wiley
            if default_publisher == 'Wiley':
                ticket['Currency of APC'] = 'GBP'
            # add discount value to notes
            if 'Prepayment discount' in ticket.keys():
                ticket['Notes'] = 'Prepayment discount: {}'.format(ticket['Prepayment discount'])
            elif default_notes:
                ticket['Notes'] = default_notes

def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def clear_debug_files(wf):
    for i in os.listdir(wf):
        if not os.path.isdir(i):
            if i[0:12] == 'Midas_debug_':
                os.remove(i)

def main(arguments):

    clear_debug_files(working_folder)
    # zenexport
    # if os.path.isdir(arguments.zenexport):
    #     zenexport = os.path.join(arguments.zenexport, get_latest_csv(arguments.zenexport))
    # else:
    #     zenexport = arguments.zenexport
    zenexport = os.path.join(working_folder, 'export-2018-11-26-1308-234063-36000022879338d5.csv')
    zen_path, zen_ext = os.path.splitext(zenexport)
    # filtered_zenexport = zen_path + '_filtered_groups' + zen_ext
    # if not arguments.all_groups:
    #     if not os.path.exists(filtered_zenexport):
    #         zendesk.output_pruned_zendesk_export(zenexport, filtered_zenexport, **{'Group': mc.ZENDESK_EXCLUDED_GROUPS})
    #     zenexport = filtered_zenexport

    # input cufs reports [filename, format, funder]
    paymentfiles = [
        # [os.path.join(working_folder, "rcuk_tiny_test.csv"), 'rcuk', 'rcuk'],
        # [os.path.join(working_folder, "RCUK_2018-08-09_all_VEJx_codes.csv"), 'rcuk', 'rcuk'],
        # [os.path.join(working_folder, "RCUK_VEAG054_2018-08-09.csv"), 'coaf', 'rcuk'],
        # [os.path.join(working_folder, 'VEAG044_2018-08-09.csv'), 'coaf', 'coaf'],
        # [os.path.join(working_folder, 'VEAG045_2018-08-09.csv'), 'coaf', 'coaf'],
        # [os.path.join(working_folder, 'VEAG050_2018-08-09_with_resolved_journals.csv'), 'coaf', 'coaf'],
        [os.path.join(working_folder, 'VEAG052_expenditures-detail_2018-11-26.csv'), 'rge', 'coaf'],
        [os.path.join(working_folder, 'VEAG054_expenditures-detail_2018-11-26.csv'), 'rge', 'rcuk'],
        [os.path.join(working_folder, 'VEJx_2018-11-12.csv'), 'rcuk', 'rcuk'],
    ]
    # other input files
    apollo_exports = [os.path.join(working_folder, "Apollo_all_items_2018-11-26.csv"), ]
    pmc_exports = [os.path.join(working_folder, "PMID_PMCID_DOI.csv"), ]



    # rep = Report(zenexport, report_type='all')
    # rep.zd_parser.index_zd_data()
    # dict_counter = 0
    # for dict in [rep.zd_parser.invoice2zd_dict]:
    #     logger.info('Analysing dict {}'.format(dict_counter))
    #     for k, v in dict.items():
    #         logger.info('k: {}; v: {}'.format(k, v))
    #     dict_counter += 1
    # raise


    # get the report object
    rep = Report(zenexport, report_type='coaf')
    rep.zd_parser.index_zd_data()
    # if not arguments.ignore_apollo:
    #     rep.plugin_apollo(apollo_exports)
    # if not arguments.ignore_pmc:
    #     rep.plugin_pmc(pmc_exports)
    # rep.parse_old_payments_spreadsheet(os.path.join(working_folder, 'LST_AllFinancialData_V3_20160721_Main_Sheet.csv'))
    rep.parse_cufs_data(paymentfiles)

    rep.populate_invoiced_articles()
    rep.populate_report_fields(report_template=mc.ReportTemplate())
    rep.output_csv()

if __name__ == '__main__':

    home = os.path.expanduser("~")
    datasources = os.path.join(home, 'OSC-shared-drive', 'OSC', 'DataSources')

    sign_off = '''-------------
Midas {}
Author: {}
Copyright (c) 2017

Midas is part of OATs. The source code and documentation can be found at
https://github.com/osc-cam/OATs

You are free to distribute this software under the terms of the GNU General Public License.  
The complete text of the GNU General Public License can be found at 
http://www.gnu.org/copyleft/gpl.html

    '''.format(__version__, __author__)
    description_text = 'Produces reports of open access and other publication charges paid from RCUK and/or COAF block grants'

    parser = argparse.ArgumentParser(description=description_text, epilog=sign_off, prog='Midas',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-a', '--ignore-apollo', dest='ignore_apollo', action='store_true',
                        help='Do not include metadata exported from Apollo (default: %(default)s)')
    parser.add_argument('-b', '--report-beginning', dest='report_start', type=valid_date,
                        default='2000-01-01', metavar='YYYY-MM-DD',
                        help='The report start date in the format YYYY-MM-DD (default: %(default)s)')
    parser.add_argument('-c', '--coaf', dest='coaf', default=True, type=bool, metavar='True or False',
                        help='Report on all APCs paid using COAF funds during the reporting period (default: %(default)s)')
    parser.add_argument('-d', '--dois', dest='dois', default=False, type=bool, metavar='True or False',
                        help='Output list of DOIs for Cottage Labs compliance check (default: %(default)s)')
    parser.add_argument('-e', '--report-end', dest='report_end', type=valid_date,
                        default='2100-01-01', metavar='YYYY-MM-DD',
                        help='The report end date in the format YYYY-MM-DD (default: %(default)s)')
    parser.add_argument('-f', '--frontiers', dest='frontiers', default=True, type=bool, metavar='True or False',
                        help='Include articles approved via Frontiers institutional account (default: %(default)s)')
    parser.add_argument('-g', '--all-groups', dest='all_groups', action='store_true',
                        help='Include Zendesk tickets in all groups (default: %(default)s). If this option is not'
                             'specified, Zendesk tickets in the following groups will be ignored after the first'
                             ' run: {}'.format(mc.ZENDESK_EXCLUDED_GROUPS))
    parser.add_argument('-l', '--cottage-labs', dest='cottage-labs', default=False, type=bool, metavar='True or False',
                        help='Include results of Cottage Labs search in output report (default: %(default)s)')
    parser.add_argument('-r', '--rcuk', dest='rcuk', default=True, type=bool, metavar='True or False',
                        help='Report on all APCs paid using RCUK funds during the reporting period (default: %(default)s)')
    parser.add_argument('-s', '--springer', dest='springer', default=True, type=bool, metavar='True or False',
                        help='Include articles approved via Springer Compact (default: %(default)s)')
    parser.add_argument('-o', '--output-folder', dest='working_folder', type=str, metavar='<path>',
                        help='Path to folder where {} should save output files (default: %(default)s)'.format(
                            '%(prog)s'),
                        default=os.path.join(home, 'OATs', 'Midas-wd'))
    parser.add_argument('-p', '--ignore-pmc', dest='ignore_pmc', action='store_true',
                        help='Do not include metadata exported from Europe PMC (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-w', '--wiley', dest='wiley', default=True, type=bool, metavar='True or False',
                        help='Include articles approved via Wiley institutional account (default: %(default)s)')
    parser.add_argument('-x', '--oxford', dest='oxford', default=True, type=bool, metavar='True or False',
                        help='Include articles approved via OUP institutional account (default: %(default)s)')
    parser.add_argument('-z', '--zendesk-export', dest='zenexport', type=str, metavar='<path>',
                        default=os.path.join(datasources, 'ZendeskExports'),
                        help='Path to csv file containing ticket data exported from zendesk. If <path> is a folder, '
                             'the most recently modified file in that folder will be used (default: %(default)s)')

    arguments = parser.parse_args()

    # working folder
    working_folder = arguments.working_folder
    working_folder = os.path.join(home, 'Dropbox', 'Midas-wd')
    if not os.path.exists(working_folder):
        os.makedirs(working_folder)

    logfilename = os.path.join(working_folder, 'midas.log')
    logging.config.fileConfig('logging.conf', defaults={'logfilename': logfilename})
    logger = logging.getLogger('midas')

    os.chdir(working_folder)

    main(arguments)