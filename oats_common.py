import os
import csv

DOI_CLEANUP = ['http://dx.doi.org/', 'https://doi.org/', 'http://dev.biologists.org/lookup/doi/', 'http://www.hindawi.com/journals/jdr/aip/2848759/']
DOI_FIX = {'0.1136/jmedgenet-2016-104295':'10.1136/jmedgenet-2016-104295'}

def get_latest_csv(folder_path):
    """ This function returns the filename of the latest modified CSV file in directory folder_path
    """
    modtimes = []
    for i in os.listdir(folder_path):
        try:
            mod = os.path.getmtime(os.path.join(folder_path, i))
            modtimes.append((mod, i))
        except FileNotFoundError:
            pass
    modtimes.sort()
    listcounter = -1
    latestfilename = modtimes[listcounter][1]
    while latestfilename[-4:].upper() not in [".CSV"]:
        listcounter = listcounter - 1
        latestfilename = modtimes[listcounter][1]
    return(latestfilename)

def prune_and_cleanup_string(string, pruning_list, typo_dict):
    '''
    A function to prune substrings from a string and/or correct typos (replace original string
    by corrected string)
    :param string: original string
    :param pruning_list: list of substrings to be replaced by an empty string
    :param typo_dict: a dictionary mapping strings to corrected strings
    :return: corrected string
    '''
    for a in pruning_list:
        string = string.replace(a, '')
    if string in typo_dict.keys():
        string = typo_dict[string]
    return(string.strip())

def action_index_zendesk_data_general(zenexport, zd_dict={}, title2zd_dict={}, doi2zd_dict={}, oa2zd_dict={}, apollo2zd_dict={}, zd2zd_dict={}):
    """ This function parses a csv file exported from the UoC OSC zendesk account
        and returns several dictionaries with the contained data

        :param zenexport: path of the csv file exported from zendesk
        :param zd_dict: dictionary representation of the data exported from zendesk
        :param title2zd_dict: dictionary matching publication titles to zendesk numbers
        :param doi2zd_dict: dictionary matching DOIs to zendesk numbers
        :param oa2zd_dict: dictionary matching OA- numbers (Avocet) to zendesk numbers
        :param apollo2zd_dict: dictionary matching Apollo handles to zendesk numbers
        :param zd2zd_dict: dictionary matching zendesk numbers to zendesk numbers
        :return: zd_dict, title2zd_dict, doi2zd_dict, oa2zd_dict, apollo2zd_dict, zd2zd_dict
    """
    with open(zenexport, encoding = "utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            zd_number = row['Id']
            oa_number = row['externalID [txt]']
            article_title = row['Manuscript title [txt]']
    #        rcuk_payment = row['RCUK payment [flag]']
    #        rcuk_policy = row['RCUK policy [flag]']
    #        apc_payment = row['Is there an APC payment? [list]']
    #        green_version = 'Green allowed version [list]'
    #        embargo = 'Embargo duration [list]'
    #        green_licence = 'Green licence [list]',
            apollo_handle = row['Repository link [txt]'].replace('https://www.repository.cam.ac.uk/handle/' , '')
            doi = prune_and_cleanup_string(row['DOI (like 10.123/abc456) [txt]'], DOI_CLEANUP, DOI_FIX)
            row['DOI (like 10.123/abc456) [txt]'] = doi
            try:
                dateutil_options = dateutil.parser.parserinfo(dayfirst=True)
                publication_date = convert_date_str_to_yyyy_mm_dd(row['Publication date (YYYY-MM-DD) [txt]'], dateutil_options)
                row['Publication date (YYYY-MM-DD) [txt]'] = publication_date
            except NameError:
                # dateutil module could not be imported (not installed)
                pass
            title2zd_dict[article_title.upper()] = zd_number
            doi2zd_dict[doi] = zd_number
            oa2zd_dict[oa_number] = zd_number
            apollo2zd_dict[apollo_handle] = zd_number
            zd2zd_dict[zd_number] = zd_number
            zd_dict[zd_number] = row
    #        if (rcuk_payment == 'yes') or (rcuk_policy) == 'yes':
    #            zd_dict_RCUK[zd_number] = row
    #            title2zd_dict_RCUK[article_title.upper()] = zd_number
        return(zd_dict, title2zd_dict, doi2zd_dict, oa2zd_dict, apollo2zd_dict, zd2zd_dict)

def extract_csv_header(inputfile, enc='utf-8'):
    '''
    This function returns a list of the fields contained in the header (first row) of
    a CSV file
    :param inputfile: path of CSV file
    :param enc: encoding of CSV file
    '''
    outputlist = []
    with open(inputfile, encoding=enc) as csvfile:
        headerreader = csv.reader(csvfile)
        # ~ print(type(headerreader))
        for row in headerreader:
            outputlist.append(row)
    return(outputlist[0])


def plug_in_payment_data(paymentsfile, fileheader, oa_number_field, output_apc_field, output_pagecolour_field, zd_dict,
                         invoice_field='Ref 5', amount_field='Amount', file_encoding='charmap',
                         transaction_code_field='Tran', source_funds_code_field='SOF', funder='RCUK'):
    '''
    This function parses financial reports produced by CUFS, then matches and appends this data to zendesk
    ticket export (zd_dict)
    :param paymentsfile: path of input CSV file containing payment data
    :param fileheader: header of input CSV file
    :param oa_number_field: name of field in input file containing "OA-" numbers
    :param output_apc_field: name of field to output summed APC payments to
    :param output_pagecolour_field: name of field to output summed page/colour payments to
    :param zd_dict: name of dictionary containing zendesk ticket data
    :param invoice_field: name of field in input file containing invoice numbers
    :param amount_field: name of field in input file containing the amount of each payment
    :param file_encoding: enconding of input file
    :param transaction_code_field: name of field in input file containing the transaction code
                                    for APC payments (EBDU) or page/colour (EBDV)
    :param source_funds_code_field: name of field in input file containing the source of funds code (JUDB)
    :param funder: funder who requested this report (e.g. RCUK / COAF)
    '''
    # t_oa_zd = re.compile("(OA)?(ZD)?[ \-]?[0-9]{4,8}")
    t_oa = re.compile("OA[ \-]?[0-9]{4,8}")
    t_zd = re.compile("ZD[ \-]?[0-9]{4,8}")
    payments_dict_apc = {}
    payments_dict_other = {}
    with open(paymentsfile, encoding=file_encoding) as csvfile:
        reader = csv.DictReader(csvfile)
        row_counter = 0
        for row in reader:
            if row[oa_number_field] in oa_number_typos.keys():
                row[oa_number_field] = oa_number_typos[row[oa_number_field]]
            # print('\n', 'oa_number_field:', oa_number_field)
            m_oa = t_oa.search(row[oa_number_field].upper())
            m_zd = t_zd.search(row[oa_number_field].upper())
            # before = row[oa_number_field]
            if m_oa:
                oa_number = m_oa.group().upper().replace("OA", "OA-").replace(" ", "")
                try:
                    zd_number = oa2zd_dict[oa_number]
                except KeyError:
                    ### MANUAL FIX FOR OLD TICKET
                    if oa_number == "OA-1128":
                        zd_number = '3743'  # DOI: 10.1088/0953-2048/27/8/082001
                    else:
                        print("WARNING: A ZD number could not be found for", oa_number, "in",
                              paymentsfile + ". Data for this OA number will NOT be exported.")
                        zd_number = ''
            elif m_zd:
                zd_number = m_zd.group().replace(" ", "-").strip('ZDzd -')
            else:
                zd_number = ''

            if row[invoice_field].strip() in invoice2zd_number.keys():
                zd_number = invoice2zd_number[row[invoice_field]]

            if row[oa_number_field].strip() in description2zd_number.keys():
                zd_number = description2zd_number[row[oa_number_field]]

            if zd_number:
                if zd_number in zd_number_typos.keys():
                    zd_number = zd_number_typos[zd_number]
                # print('zd_number:', zd_number)
                if transaction_code_field in row.keys():
                    ##PAYMENTS SPREADSHEET CONTAINS TRANSACTION FIELD
                    if row[source_funds_code_field] == 'JUDB':
                        if row[transaction_code_field] == 'EBDU':
                            if funder == 'RCUK':
                                key = 'EBDU_' + str(row_counter)
                                included_rcuk_payment_dict[key] = row.copy()
                            if zd_number in payments_dict_apc.keys():
                                ### ANOTHER APC PAYMENT WAS ALREADY RECORDED FOR THIS ZD
                                ### NUMBER, SO WE CONCATENATE VALUES
                                existing_payment = payments_dict_apc[zd_number]
                                p_amount = float(existing_payment[output_apc_field].replace(',', ''))
                                n_amount = float(row[amount_field].replace(',', ''))
                                balance = str(p_amount + n_amount)
                                for k in row.keys():
                                    if (existing_payment[k] != row[k]) and (k not in [rcuk_paydate_field,
                                                                                      coaf_paydate_field]):  # DO NOT CONCATENATE PAYMENT DATES
                                        n_value = existing_payment[k] + ' %&% ' + row[k]
                                    else:
                                        n_value = row[k]
                                    payments_dict_apc[zd_number][k] = n_value
                                payments_dict_apc[zd_number][output_apc_field] = balance
                            else:
                                ###STORE APC PAYMENT INFO INDEXED ON ZD NUMBER
                                payments_dict_apc[zd_number] = row
                                payments_dict_apc[zd_number][output_apc_field] = payments_dict_apc[zd_number][
                                    amount_field]
                            ### NOW THAT WE DEALT WITH THE PROBLEM OF SEVERAL APC PAYMENTS
                            ### FOR EACH ZD NUMBER, ADD PAYMENT INFO TO MASTER DICT
                            ### OF ZD NUMBERS
                            for field in payments_dict_apc[zd_number].keys():
                                if (field in zd_dict[zd_number].keys()) and (row_counter == 0):
                                    print('WARNING: Dictionary for ZD ticket', zd_number,
                                          'already contains a field named',
                                          field + '. It will be overwritten by the value in file', paymentsfile)
                            zd_dict[zd_number].update(payments_dict_apc[
                                                          zd_number])  # http://stackoverflow.com/questions/8930915/append-dictionary-to-a-dictionary
                        elif row[transaction_code_field] in ['EBDV', 'EBDW']:
                            if funder == 'RCUK':
                                key = 'EBDV-W_' + str(row_counter)
                                included_rcuk_payment_dict[key] = row.copy()
                            if zd_number in payments_dict_other.keys():
                                ### ANOTHER PAGE/MEMBERSHIP PAYMENT WAS ALREADY RECORDED FOR THIS ZD
                                ### NUMBER, SO WE CONCATENATE VALUES
                                existing_payment = payments_dict_other[zd_number]
                                p_amount = float(existing_payment[output_pagecolour_field].replace(',', ''))
                                n_amount = float(row[amount_field].replace(',', ''))
                                balance = str(p_amount + n_amount)
                                for k in row.keys():
                                    if (existing_payment[k] != row[k]) and (
                                        k not in [rcuk_paydate_field, coaf_paydate_field, transaction_code_field]):
                                        n_value = existing_payment[k] + ' %&% ' + row[k]
                                    elif k == transaction_code_field:  # special treatment for this case necessary to avoid overwriting preexisting APC transaction code (EBDU); concatenate with value in apc dict
                                        try:
                                            if payments_dict_apc[zd_number][k]:
                                                n_value = payments_dict_apc[zd_number][k] + ' %&% ' + row[k]
                                            else:
                                                n_value = row[k]
                                        except KeyError:
                                            n_value = row[k]
                                    else:
                                        n_value = row[k]
                                    payments_dict_other[zd_number][k] = n_value
                                payments_dict_other[zd_number][output_pagecolour_field] = balance
                            else:
                                ###STORE PAGE/MEMBERSHIP PAYMENT INFO INDEXED ON ZD NUMBER
                                payments_dict_other[zd_number] = row
                                payments_dict_other[zd_number][output_pagecolour_field] = \
                                payments_dict_other[zd_number][amount_field]
                            ### NOW THAT WE DEALT WITH THE PROBLEM OF SEVERAL PAGE/MEMBERSHIP PAYMENTS
                            ### FOR EACH ZD NUMBER, ADD PAYMENT INFO TO MASTER DICT
                            ### OF ZD NUMBERS
                            for field in payments_dict_other[zd_number].keys():
                                if (field in zd_dict[zd_number].keys()) and (row_counter == 0):
                                    print('WARNING: Dictionary for ZD ticket', zd_number,
                                          'already contains a field named',
                                          field + '. It will be overwritten by the value in file', paymentsfile)
                            zd_dict[zd_number].update(payments_dict_other[
                                                          zd_number])  # http://stackoverflow.com/questions/8930915/append-dictionary-to-a-dictionary
                        else:
                            ## NOT A EBDU, EBDV OR EBDW PAYMENT
                            key = 'not_EBD*_payment_' + str(row_counter)
                            if funder == 'RCUK':
                                rejected_rcuk_payment_dict[key] = row
                            debug_filename = nonEBDU_payment_file_prefix + paymentsfile
                            output_debug_info(debug_filename, row, fileheader)
                    else:
                        ## NOT A JUDB PAYMENT
                        key = 'not_JUDB_payment_' + str(row_counter)
                        if funder == 'RCUK':
                            rejected_rcuk_payment_dict[key] = row
                        debug_filename = nonJUDB_payment_file_prefix + paymentsfile
                        output_debug_info(debug_filename, row, fileheader)
                else:
                    ##PAYMENTS SPREADSHEET DOES NOT CONTAIN TRANSACTION FIELD
                    ##WE MUST ASSUME ALL PAYMENTS ARE APCs
                    key = 'no_transaction_field_' + str(row_counter)
                    if funder == 'RCUK':
                        rejected_rcuk_payment_dict[key] = row
                    if zd_number in payments_dict_apc.keys():
                        ### ANOTHER APC PAYMENT WAS ALREADY RECORDED FOR THIS ZD
                        ### NUMBER, SO WE CONCATENATE VALUES
                        existing_payment = payments_dict_apc[zd_number]
                        p_amount = float(existing_payment[output_apc_field].replace(',', ''))
                        n_amount = float(row[amount_field].replace(',', ''))
                        balance = str(p_amount + n_amount)
                        for k in row.keys():
                            if (existing_payment[k] != row[k]) and (k not in [rcuk_paydate_field, coaf_paydate_field]):
                                n_value = existing_payment[k] + ' %&% ' + row[k]
                            else:
                                n_value = row[k]
                            payments_dict_apc[zd_number][k] = n_value
                        payments_dict_apc[zd_number][output_apc_field] = balance
                    else:
                        ###STORE APC PAYMENT INFO INDEXED ON ZD NUMBER
                        payments_dict_apc[zd_number] = row
                        try:
                            payments_dict_apc[zd_number][output_apc_field] = payments_dict_apc[zd_number][amount_field]
                        except KeyError:
                            print('WARNING: Could not determine amount of payment for ticket below. Using ZERO:')
                            pprint(payments_dict_apc[zd_number])
                            payments_dict_apc[zd_number][output_apc_field] = '0'
                    ### NOW THAT WE DEALT WITH THE PROBLEM OF SEVERAL APC PAYMENTS
                    ### FOR EACH ZD NUMBER, ADD PAYMENT INFO TO MASTER DICT
                    ### OF ZD NUMBERS
                    for field in payments_dict_apc[zd_number].keys():
                        if (field in zd_dict[zd_number].keys()) and (row_counter == 0):
                            print('WARNING: Dictionary for ZD ticket', zd_number, 'already contains a field named',
                                  field + '. It will be overwritten by the value in file', paymentsfile)
                    zd_dict[zd_number].update(payments_dict_apc[
                                                  zd_number])  # http://stackoverflow.com/questions/8930915/append-dictionary-to-a-dictionary
            else:
                ## PAYMENT COULD NOT BE LINKED TO A ZENDESK NUMBER
                key = 'no_zd_match_' + str(row_counter)
                if funder == 'RCUK':
                    rejected_rcuk_payment_dict[key] = row
                debug_filename = unmatched_payment_file_prefix + paymentsfile
                output_debug_info(debug_filename, row, fileheader)
            row_counter += 1