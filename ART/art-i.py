#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import art
import os
import csv
import sys
from pprint import pprint

if __name__ == '__main__':
    ### SET UP WORKING FOLDER AND MAIN VARIABLES
    home = os.path.expanduser("~")
    working_folder = os.path.join(home, 'OATs', 'ART-wd')
    zendesk_export = os.path.join(working_folder, 'zendesk-export-2017-04-19-1127-4115070e8d.csv')
    apollo_export = os.path.join(working_folder, 'LST_ApolloOAOutputs_v3_20170504.csv')
    row2zd_number_file = 'ART-row_to_ZD_number.csv'
    output_fields = []
    zd_dict = {}
    titles_not_matching_ZD_in_previous_run = []
    titles_from_previous_run_file = 'ART_info_add_to_exclusion_list_because_not_in_funders_policy_.txt'
    if titles_from_previous_run_file in os.listdir():
        for title in open(titles_from_previous_run_file):
            titles_not_matching_ZD_in_previous_run.append(title.strip())

    ### TO BE IMPLEMENTED: ASK USER TO SELECT OUTPUT FIELDS FROM THOSE AVAILABLE IN INPUT FILE
    ### FOR NOW, LET'S USE ALL FIELDS
    print('\n')
    input_csv_filename = sys.argv[1]
    input_title_field = ''
    input_doi_field = ''
    input_oa_field = ''
    input_apollo_field = ''
    input_zd_field = ''
    header = art.extract_csv_header(input_csv_filename)
    for column in header:
        if column.upper() in ['DOI', 'DOIS', 'DIGITAL OBJECT IDENTIFIER', 'DIGITAL OBJECT IDENTIFIER (DOI)', 'DIGITAL OBJECT IDENTIFIERS (DOI)']:
            input_doi_field = column
        if column.upper() in ['ARTICLE TITLE', 'TITLE', 'PUBLICATION TITLE', 'MANUSCRIPT TITLE']:
            input_title_field = column
        #TO BE IMPLEMENTED: DETECTION OF OTHER KEY FIELDS AND PROMPTING USER IF AUTOMATIC DETECTION FAILS
        print(header.index(column), '\t', column)
    output_fields += header

    ###POPULATE DICTIONARIES
    (zd_dict, title2zd_dict, doi2zd_dict, oa2zd_dict, apollo2zd_dict, zd2zd_dict) = art.action_index_zendesk_data_general(zendesk_export)
    doi2apollo = art.action_populate_doi2apollo(apollo_export)
    row2zd_number = {}
    if row2zd_number_file in os.listdir():
        for row in open(row2zd_number_file):
            a = row.split('\t')
            row2zd_number[a[0]] = a[1]

    output_dict = {}
    output_row2zd_number = open(row2zd_number_file, 'w')
    ###MATCH EACH ROW OF INPUT FILE TO A ZENDEK TICKET (ZD_DICT ENTRY) AND MERGE THE DATA IN A SINGLE DICT
    with open(input_csv_filename) as csvfile:
        reader = csv.DictReader(csvfile)
        row_counter = 0
        for row in reader:
            output_dict[row_counter] = row
            doi = row[input_doi_field]
            title = row[input_title_field]
            publisher = ''
            if row_counter in row2zd_number.keys():
                zd_number = row2zd_number[row_counter]
            else:
                if not title in titles_not_matching_ZD_in_previous_run:
                    (zd_number, fail_reason) = art.match_prepayment_deal_to_zd(doi, title, publisher, doi2zd_dict, doi2apollo, apollo2zd_dict, title2zd_dict, institution='University of Cambridge', restrict_to_rcuk_policy=False)
                else:
                    print('ART0-I: Previous run did not return a ZD match; skipping')
                    zd_number = ''
            if zd_number:
                print('art-i: detected zd_number:', zd_number)
                output_row2zd_number.write(str(row_counter) + '\t' + zd_number + '\n')
                output_dict[row_counter].update(zd_dict[zd_number])
            else:
                print('art-i: zd_number could not be found for row', row_counter)
            row_counter += 1
    output_row2zd_number.close()

    ###CHOOSE ADDITIONAL OUTPUT FIELDNAMES
    funders_report_fieldnames = ['COAF policy [flag]', 'COAF payment [flag]', 'Arthritis Research UK [flag]',
                                 'Bloodwise (Leukaemia & Lymphoma Research) [flag]', 'Breast Cancer Campaign [flag]',
                                 'British Heart Foundation [flag]', 'Cancer Research UK [flag]', "Parkinson's UK [flag]",
                                 'Wellcome Trust [flag]', 'RCUK policy [flag]', 'RCUK payment [flag]', 'AHRC [flag]',
                                 'BBSRC [flag]', 'EPSRC [flag]', 'NERC [flag]', 'MRC [flag]', 'STFC [flag]']
    output_fields += funders_report_fieldnames

    ###OUTPUT CSV FILE CONTAINING THE FIELDS OF INTEREST
    with open('art-i_output_report.csv') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=output_fields, extrasaction='ignore')
        writer.writeheader()
        for row in output_dict:
            writer.writerow(output_dict[row])