#!/usr/bin/env python3

import csv
import os
import pandas as pd
import re
import time
from pprint import pprint
import subprocess

from common import zendesk, cufs
from midas import ZENDESK_EXCLUDED_GROUPS



data_sources = '/home/asartori/OATs/Midas-DataSources'
#data_sources = 'L:\OSC\DataSources\ZendeskExports'
zd_file = 'export-2018-04-20-1120-234063-360000053233b409.csv'
# zd_file = 'test_10000_lines.csv'
#zd_file = 'cropping_test.csv'
cufs_export_type = 'RCUK'
paymentsfile = 'VEJJ/VEJJ_2017-10-31.csv'

zenexport = os.path.join(data_sources, 'ZendeskExports', zd_file)

parse_zd_fieldnames(zenexport)
raise

# # CSV VERSUS PANDAS
# with open(zenexport, encoding="utf-8") as csvfile:
#     data = []
#     reader = csv.DictReader(csvfile)
#     for row in reader:
#         data.append(row)
# print('csv.DictReader finished after {} seconds'.format(time.time() - start_time))
# start_time = time.time()
df = pd.read_csv(zenexport)
# data = df.values
pprint(df)
print('Pandas finished after {} seconds'.format(time.time() - start_time))


# TEST FUNCTION output_pruned_zendesk_export
#zendesk.output_pruned_zendesk_export(zenexport, 'cropping_test.csv', **{'Group':ZENDESK_EXCLUDED_GROUPS})


# TEST ZENDESK PARSER
# a = zendesk.Parser()
# a.index_zd_data(zenexport)
# with_title_counter = 0
# without_title_counter = 0
# for k, v in a.zd_dict.items():
#     if v.metadata['Manuscript title [txt]'] not in ['', '-']:
#         with_title_counter += 1
#     else:
#         without_title_counter +=1
# print('Total with title: {}'.format(with_title_counter))
# print('Total without title: {}'.format(without_title_counter))
#a.plug_in_payment_data(cufs_export_type, paymentsfile)
print('Finished after {} seconds'.format(time.time() - start_time))

