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
from pprint import pprint
from difflib import SequenceMatcher

import common.cufs as cufs
import common.midas_constants as mc
import common.zendesk as zendesk
from common.oatsutils import extract_csv_header, get_latest_csv

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

        self.springer = True
        self.wiley = True
        self.oup = True
        self.frontiers = True
        self.zd_parser = zendesk.Parser(zenexport)

        self.fieldnames = fieldnames
        self.articles=[]

    def parse_cufs_data(self, cufs_datasources=None):
        '''
        Populates self.zd_parser.zd_dict with data from CUFS reports

        :param cufs_datasources: An array of CUFS reports, each being a list in the format [filename, format, funder]
        '''
        if not self.zd_parser.zd_dict.keys():
            self.zd_parser.index_zd_data()
        for datasource in cufs_datasources:
            logger.info('Parsing CUFS report {}'.format(datasource))
            self.zd_parser.plug_in_payment_data(datasource[0], datasource[1], datasource[2])

def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

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
                    help='Path to folder where {} should save output files (default: %(default)s)'.format('%(prog)s'),
                    default=os.path.join(home, 'OATs', 'Midas-wd'))
parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('-w', '--wiley', dest='wiley', default=True, type=bool, metavar='True or False',
                    help='Include articles approved via Wiley institutional account (default: %(default)s)')
parser.add_argument('-x', '--oxford', dest='oxford', default=True, type=bool, metavar='True or False',
                    help='Include articles approved via OUP institutional account (default: %(default)s)')
parser.add_argument('-z', '--zendesk-export', dest='zenexport', type=str, metavar='<path>',
                    default=os.path.join(datasources, 'ZendeskExports'),
                    help='Path to csv file containing ticket data exported from zendesk. If <path> is a folder, '
                         'the most recently modified file in that folder will be used (default: %(default)s)')

if __name__ == '__main__':
    arguments = parser.parse_args()

    # working folder
    working_folder = arguments.working_folder
    if not os.path.exists(working_folder):
        os.makedirs(working_folder)

    logfilename = os.path.join(working_folder, 'midas.log')
    logging.config.fileConfig('logging.conf', defaults={'logfilename': logfilename})
    logger = logging.getLogger('midas')

    # zenexport
    # if os.path.isdir(arguments.zenexport):
    #     zenexport = os.path.join(arguments.zenexport, get_latest_csv(arguments.zenexport))
    # else:
    #     zenexport = arguments.zenexport
    zenexport = os.path.join(working_folder, 'export-2018-08-13-1310-234063-3600001227941889.csv')
    zen_path, zen_ext = os.path.splitext(zenexport)
    filtered_zenexport = zen_path + '_filtered_groups' + zen_ext
    if not arguments.all_groups:
        if not os.path.exists(filtered_zenexport):
            zendesk.output_pruned_zendesk_export(zenexport, filtered_zenexport, **{'Group':mc.ZENDESK_EXCLUDED_GROUPS})
        zenexport = filtered_zenexport

    # input cufs reports [filename, format, funder]
    paymentfiles = [
        [os.path.join(working_folder, "RCUK_2018-08-09_all_VEJx_codes.csv"), 'rcuk', 'rcuk'],
        [os.path.join(working_folder, "RCUK_VEAG054_2018-08-09.csv"), 'coaf', 'rcuk'],
        [os.path.join(working_folder, 'VEAG044_2018-08-09.csv'), 'coaf', 'coaf'],
        [os.path.join(working_folder, 'VEAG045_2018-08-09.csv'), 'coaf', 'coaf'],
        [os.path.join(working_folder, 'VEAG050_2018-08-09_with_resolved_journals.csv'), 'coaf', 'coaf'],
        [os.path.join(working_folder, 'VEAG052_2018-08-09.csv'), 'coaf', 'coaf'],
    ]

    # get the report object
    rep = Report(zenexport, report_type='all')
    rep.parse_cufs_data(paymentfiles)