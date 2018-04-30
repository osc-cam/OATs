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
try:
    import dateutil.parser
except ModuleNotFoundError:
    print('WARNING: Could not load the dateutil module. Please install it if you have admin rights. Conversion of dates will not work properly during this run')
import collections
from pprint import pprint
from difflib import SequenceMatcher

class Report():
    '''
    The report object
    '''

    def __init__(self):
        self.period_start = datetime.datetime(2000, 1, 1)
        self.period_end = datetime.datetime.now().date()
        self.report_rcuk = True
        self.report_coaf = True
        self.report_springer = True
        self.report_wiley = True
        self.report_oup = True
        self.report_frontiers = True

    



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
                    help='Do not include metadata exported from Apollo')
parser.add_argument('-c', '--coaf', dest='coaf', default=True, type=bool, metavar='True or False',
                    help='Report on all APCs paid using COAF funds during the reporting period')
parser.add_argument('-d', '--dois', dest='dois', default=False, type=bool, metavar='True or False',
                    help='Output list of DOIs for Cottage Labs compliance check')
parser.add_argument('-l', '--cottage-labs', dest='cottage-labs', default=False, type=bool, metavar='True or False',
                    help='Include results of Cottage Labs search in output report')
parser.add_argument('-r', '--rcuk', dest='rcuk', default=True, type=bool, metavar='True or False',
                    help='Report on all APCs paid using RCUK funds during the reporting period')
parser.add_argument('-o', '--output-folder', dest='working_folder', type=str, metavar='<path>',
                    help='Path to folder where {} should save output files'.format('%(prog)s'),
                    default=os.path.join(os.path.expanduser("~"), 'OATs', 'Midas-wd'))
parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
arguments = parser.parse_args()

working_folder = arguments.working_folder
if not os.path.exists(working_folder):
    os.makedirs(working_folder)

