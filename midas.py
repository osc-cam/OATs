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
from pprint import pprint
from difflib import SequenceMatcher

import common.zendesk as zendesk
from common.oatsutils import get_latest_csv

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


class Report():
    '''
    The report object
    '''

    def __init__(self):
        self.period_start = datetime.datetime(2000, 1, 1)
        self.period_end = datetime.datetime.now().date()
        self.rcuk = True
        self.coaf = True
        self.springer = True
        self.wiley = True
        self.oup = True
        self.frontiers = True
        self.zd_parser = zendesk.Parser()
    

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
                         ' run: {}'.format(ZENDESK_EXCLUDED_GROUPS))
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

    working_folder = arguments.working_folder
    if not os.path.exists(working_folder):
        os.makedirs(working_folder)

    if os.path.isdir(arguments.zenexport):
        zenexport = os.path.join(arguments.zenexport, get_latest_csv(arguments.zenexport))
    else:
        zenexport = arguments.zenexport

    zen_path, zen_ext = os.path.splitext(zenexport)
    filtered_zenexport = zen_path + '_filtered_groups' + zen_ext
    if not arguments.all_groups:
        if not os.path.exists(filtered_zenexport):
            zendesk.output_pruned_zendesk_export(zenexport, filtered_zenexport, **{'Group':ZENDESK_EXCLUDED_GROUPS})
        zenexport = filtered_zenexport

    rep = Report()