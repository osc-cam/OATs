import csv
import time
import subprocess

import zendesk
import cufs

start_time = time.time()
a = zendesk.Parser()
c = cufs.Parser({'OA-156':'567'})
# #zd_file = 'L:\OSC\DataSources\ZendeskExports\export-2018-04-20-1120-234063-360000053233b409.csv'
zd_file = '/home/asartori/OSC-shared-drive/OSC/DataSources/ZendeskExports/export-2018-04-20-1120-234063-360000053233b409.csv'
# dicts = a.index_zd_data(zd_file)
print('Finished after {} seconds'.format(time.time() - start_time))

