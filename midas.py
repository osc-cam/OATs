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
parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('-o', '--output-folder', dest='working_folder', type=str, metavar='<path>',
                    help='Path to folder where {} should save output files'.format('%(prog)s'),
                    default=os.path.join(os.path.expanduser("~"), 'OATs', 'Midas-wd'))
arguments = parser.parse_args()

working_folder = arguments.working_folder
if not os.path.exists(working_folder):
    os.makedirs(working_folder)

