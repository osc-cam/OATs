#!/usr/bin/env python3

## Ideas
# - arguments for reporting period, type of report to generate

__version__ = '2019.01'
__author__ = 'André Sartori'

"""
Simple script to filter a CSV export downloaded from Zendesk
"""

import argparse
import datetime
import logging
import logging.config
import os

from common.oatsutils import get_latest_csv
from common.zendesk import filter_zendesk_export as zd_filter
from common.zendesk import ZdFieldsMapping as FieldMap

FM = FieldMap()

USER_QUERY = {FM.wellcome_trust: 'yes'}

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

def main(arguments):
    if os.path.isdir(arguments.zenexport):
        zenexport = os.path.join(arguments.zenexport, get_latest_csv(arguments.zenexport))
    else:
        zenexport = arguments.zenexport

    output_filename = '{}_filtered_zendesk_export.csv'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    zd_filter(zenexport, output_filename, **USER_QUERY)

if __name__ == '__main__':

    home = os.path.expanduser("~")
    datasources = os.path.join(home, 'OSC-shared-drive', 'OSC', 'DataSources')

    sign_off = '''-------------
filter_zendesk_export {}
Author: {}
Copyright (c) 2019

filter_zendesk_export is part of OATs. The source code and documentation can be found at
https://github.com/osc-cam/OATs

You are free to distribute this software under the terms of the GNU General Public License.  
The complete text of the GNU General Public License can be found at 
http://www.gnu.org/copyleft/gpl.html

    '''.format(__version__, __author__)
    description_text = 'Simple script to filter a CSV export downloaded from Zendesk'

    parser = argparse.ArgumentParser(description=description_text, epilog=sign_off, prog='filter_zendesk_export',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output-folder', dest='working_folder', type=str, metavar='<path>',
                        help='Path to folder where {} should save output files (default: %(default)s)'.format(
                            '%(prog)s'),
                        default=os.path.join(home, 'OATs'))
    parser.add_argument('--zendesk-export', dest='zenexport', type=str, metavar='<path>',
                        default=os.path.join(datasources, 'ZendeskExports'),
                        help='Path to csv file containing ticket data exported from zendesk. If <path> is a folder, '
                             'the most recently modified file in that folder will be used (default: %(default)s)')

    arguments = parser.parse_args()
    working_folder = arguments.working_folder
    if not os.path.exists(working_folder):
        os.makedirs(working_folder)

    logfilename = os.path.join(working_folder, 'filter_zendesk_export.log')
    logging.config.fileConfig('logging.conf', defaults={'logfilename': logfilename})
    logger = logging.getLogger('filter_zendesk_export')

    os.chdir(working_folder)

    main(arguments)