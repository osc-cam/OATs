#!/usr/bin/env python3

"""
Extracts a list of unique supplier names from reports exported from CUFS
"""

import csv
import logging
import logging.config
import os
import sys
from common.cufs import CoafFieldsMapping, RcukFieldsMapping, RgeFieldsMapping

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


if __name__ == '__main__':

    home = os.path.expanduser("~")
    working_folder = os.path.join(home, "OATs", "cufs-reports")

    logfilename = os.path.join(working_folder, 'suppliers.log')
    logging.config.fileConfig('logging.conf', defaults={'logfilename': logfilename})
    logger = logging.getLogger('suppliers')

    os.chdir(working_folder)

    paymentfiles = [
        [os.path.join(working_folder, 'RCUK_2018-08-09_all_VEJx_codes.csv'), 'rcuk', 'rcuk'],
        [os.path.join(working_folder, 'VEAG044_2018-08-09.csv'), 'coaf', 'coaf'],
        [os.path.join(working_folder, 'VEAG045_2018-08-09.csv'), 'coaf', 'coaf'],
        [os.path.join(working_folder, 'VEAG050_2018-08-09_with_resolved_journals.csv'), 'coaf', 'coaf'],
        [os.path.join(working_folder, 'VEAG052_2019-01-24.csv'), 'coaf', 'coaf'],
        [os.path.join(working_folder, 'VEAG054_GMS__Actual_Expenditure_Enquir_260619.csv'), 'coaf', 'rcuk'],
        [os.path.join(working_folder, 'VEAG055_expenditures-detail_2019-07-10.csv'), 'rge', 'coaf'],
        [os.path.join(working_folder, 'VEAG060_expenditures-detail_2019-07-10.csv'), 'rge', 'rcuk'],
    ]

    suppliers = {}
    general_counter = 0

    for f in paymentfiles:
        cufs_export_type = f[1]
        if cufs_export_type == 'rcuk':
            cufs_map = RcukFieldsMapping()
        elif cufs_export_type == 'coaf':
            cufs_map = CoafFieldsMapping()
        elif cufs_export_type == 'rge':
            cufs_map = RgeFieldsMapping()
        else:
            sys.exit('{} is not a supported type of financial report (cufs_export_type)'.format(cufs_export_type))

        with open(f[0]) as csvfile:
            reader = csv.DictReader(csvfile)
            row_counter = 0
            for row in reader:
                logger.debug('-------------- {} [{}] Working on {} row: {}'.format(general_counter, row_counter,
                                                                                   csvfile, row))
                sup_key = row[cufs_map.supplier].lower().strip()
                if sup_key:
                    amount = float(row[cufs_map.amount_field].replace(',', ''))
                    if sup_key not in suppliers.keys():
                        suppliers[sup_key] = {"Supplier name": row[cufs_map.supplier], "Total amount": amount}
                    else:
                        suppliers[sup_key]["Total amount"] += amount
                row_counter += 1
                general_counter += 1

    with open(os.path.join(working_folder, "suppliers.csv"), "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Supplier name", "Total amount"])
        writer.writeheader()
        for s in suppliers:
            out_s = suppliers[s]
            writer.writerow(out_s)
            # writer.writerow([out_s])
            logger.debug("Output: {}".format(out_s))

    logger.info("Finished processing {} transactions".format(general_counter + 1))
