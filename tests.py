#!/usr/bin/env python3

import csv
import time
from pprint import pprint
import subprocess

from common import zendesk, cufs

start_time = time.time()

# TEST ZENDESK PARSER
a = zendesk.Parser()
# zd_file = 'L:\OSC\DataSources\ZendeskExports\export-2018-04-20-1120-234063-360000053233b409.csv'
zd_file = '/home/asartori/OSC-shared-drive/OSC/DataSources/ZendeskExports/export-2018-04-20-1120-234063-360000053233b409.csv'
# zd_file = '/home/asartori/OSC-shared-drive/OSC/DataSources/ZendeskExports/test_10000_lines.csv'
cufs_export_type = 'RCUK'
paymentsfile = '/home/asartori/OSC-shared-drive/OSC/DataSources/FinanceReports/VEJJ/VEJJ_2017-10-31.csv'
a.index_zd_data(zd_file)
with_title_counter = 0
without_title_counter = 0
for k, v in a.zd_dict.items():
    if v.zd_data['Manuscript title [txt]'] not in ['', '-']:
        with_title_counter += 1
    else:
        without_title_counter +=1
print('Total with title: {}'.format(with_title_counter))
print('Total without title: {}'.format(without_title_counter))
#a.plug_in_payment_data(cufs_export_type, paymentsfile)
print('Finished after {} seconds'.format(time.time() - start_time))

