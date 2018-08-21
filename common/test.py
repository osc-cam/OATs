import logging
import logging.config
import os

import zendesk
from oatsutils import extract_csv_header

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

home = os.path.expanduser("~")
working_folder = os.path.join(home, 'Dropbox', 'OSC', 'ART-wd')
zenexport = os.path.join(working_folder, 'export-2018-08-13-1310-234063-3600001227941889.csv')
paymentfile = os.path.join(working_folder, 'RCUK_2018-08-09_all_VEJx_codes.csv')

def test_zendesk_integration():
    parser = zendesk.Parser(zenexport)
    parser.index_zd_data()
    parser.plug_in_payment_data('RCUK', paymentfile)
    print(len(parser.zd_dict_with_payments.keys()))


report_template = os.path.join(working_folder, "Jisc_template_v4.csv")
report_fields = extract_csv_header(report_template, "utf-8")
print(report_fields)
custom_rep_fields = ['id',  # ZD number from zd
                     '#externalID [txt]',  # OA number from zd
                     'Reason for exclusion',  # field calculated and appended by ART
                     # 'Description',             # field from CUFS (RCUK)
                     # 'Ref 1',                   # field from CUFS (RCUK)
                     # 'Ref 5',                   # field from CUFS (RCUK)
                     'Comment',  # field from CUFS (COAF)
                     'Invoice',  # field from CUFS (COAF)
                     'RCUK policy [flag]',  # from zd
                     'RCUK payment [flag]',  # from zd
                     'COAF policy [flag]',  # from zd
                     'COAF payment [flag]',  # from zd
                     'handle'  # from Apollo
                     ]
report_fieldnames = report_fields + custom_rep_fields