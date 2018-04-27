import csv
import cufs
import datetime
import dateutil.parser
import logging
import sys
from oatsutils import extract_csv_header, output_debug_csv, prune_and_cleanup_string, DOI_CLEANUP, DOI_FIX

### USE THIS DICTIONARY TO FORCE THE MAPPING OF PARTICULARLY PROBLEMATIC OA NUMBERS TO ZD NUMBERS
### FOR EXAMPLE A OA NUMBER MARKED AS DUPLICATE IN ZENDESK, BUT WITH A PAYMENT ASSOCIATED WITH IT
### (SO NOT EASY TO FIX IN ZENDESK)
manual_oa2zd_dict = {
    # 'OA-13907':'83033',
    # 'OA-10518':'36495',
    # 'OA-13111':'76842',
    # 'OA-14062':'86232',
    # 'OA-13919':'83197',
    # 'OA-14269':'89212'
    }

unmatched_payment_file_prefix = 'Midas_debug_payments_not_matched_to_zd_numbers__'
nonJUDB_payment_file_prefix = 'Midas_debug_non_JUDB_payments__'
nonEBDU_payment_file_prefix = 'Midas_debug_non_EBDU_EBDV_or_EBDW_payments__'

class ZdFieldsMapping():
    '''
    A mapping of current Zendesk field names.
    Used to faciliate updating OATs when ZD field names are updated.
    '''
    def __init__(self):
        self.apc_payment = 'Is there an APC payment? [list]'
        self.coaf_payment = 'COAF payment [flag]'
        self.coaf_policy = 'COAF policy [flag]'
        self.doi = 'DOI (like 10.123/abc456) [txt]'
        self.duplicate = 'Duplicate [flag]'
        self.duplicate_of = 'Duplicate of (ZD-123456) [txt]'
        self.embargo = 'Embargo duration [list]'
        self.external_id = 'externalID [txt]'
        self.green_allowed_version = 'Green allowed version [list]'
        self.green_licence = 'Green licence [list]'
        self.id = 'Id'
        self.manuscript_title = 'Manuscript title [txt]'
        self.publication_date = 'Publication date (YYYY-MM-DD) [txt]'
        self.rcuk_payment = 'RCUK payment [flag]'
        self.rcuk_policy = 'RCUK policy [flag]'
        self.repository_link = 'Repository link [txt]'

class Parser():
    '''
    Parser for Zendesk CSV exports.
    Use this class to read in data exported from Zendesk and parse it into a number of
    dictionaries.
    '''
    def __init__(self):
        self.apollo2zd_dict = {}
        self.cufs_map = None
        self.doi2zd_dict = {}
        self.oa2zd_dict = {}
        self.parsed_payments = {}
        self.rejected_payments = {}
        self.title2zd_dict = {}
        self.title2zd_dict_COAF = {}
        self.title2zd_dict_RCUK = {}
        self.zd2oa_dups_dict = {}
        self.zd2zd_dict = {}
        self.zd_dict = {}
        self.zd_dict_COAF = {}
        self.zd_dict_RCUK = {}
        self.zd_fields = ZdFieldsMapping()

    def index_zd_data(self, zenexport):
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

        def convert_date_str_to_yyyy_mm_dd(string, dateutil_options):
            '''
            Function to convert dates to format YYYY-MM-DD
            :param string: original date string
            :param dateutil_options: options to be passed to dateutil
            :return: converted date or empty string if failed to convert
            '''
            try:
                d = dateutil.parser.parse(string, dateutil_options)
            except ValueError:
                d = datetime.datetime(1, 1, 1)
            d = d.strftime('%Y-%m-%d')
            if d == '1-01-01':
                return ('')
            else:
                return (d)

        with open(zenexport, encoding = "utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                zd_number = row[self.zd_fields.id]
                dup_of = row[self.zd_fields.duplicate_of]
                oa_number = row[self.zd_fields.external_id]
                article_title = row[self.zd_fields.manuscript_title].upper()
                rcuk_payment = row[self.zd_fields.rcuk_payment]
                rcuk_policy = row[self.zd_fields.rcuk_policy]
                coaf_payment = row[self.zd_fields.coaf_payment]
                coaf_policy = row[self.zd_fields.coaf_policy]
                # apc_payment = row[self.zd_fields.apc_payment]
                # green_version = row[self.zd_fields.green_allowed_version]
                # embargo = row[self.zd_fields.embargo]
                # green_licence = row[self.zd_fields.green_licence]
                apollo_handle = row[self.zd_fields.repository_link].replace('https://www.repository.cam.ac.uk/handle/' , '')
                doi = prune_and_cleanup_string(row[self.zd_fields.doi], DOI_CLEANUP, DOI_FIX)
                row[self.zd_fields.doi] = doi
                dateutil_options = dateutil.parser.parserinfo(dayfirst=True)
                publication_date = convert_date_str_to_yyyy_mm_dd(row[self.zd_fields.publication_date], dateutil_options)
                row[self.zd_fields.publication_date] = publication_date
                if article_title not in ['', '-']:
                    if article_title in self.title2zd_dict.keys():
                        self.title2zd_dict[article_title].append(zd_number)
                    else:
                        self.title2zd_dict[article_title] = [zd_number]
                if doi not in ['', '-']:
                    if (doi in self.doi2zd_dict.keys()) and self.doi2zd_dict[doi]:
                        self.doi2zd_dict[doi].append(zd_number)
                    else:
                        self.doi2zd_dict[doi] = [zd_number]
                self.oa2zd_dict[oa_number] = zd_number
                self.apollo2zd_dict[apollo_handle] = zd_number
                self.zd2zd_dict[zd_number] = zd_number
                self.zd_dict[zd_number] = row
                if (rcuk_payment == 'yes') or (rcuk_policy == 'yes'):
                    self.zd_dict_RCUK[zd_number] = row
                    self.title2zd_dict_RCUK[article_title.upper()] = zd_number
                if (coaf_payment == 'yes') or (coaf_policy == 'yes'):
                    self.zd_dict_COAF[zd_number] = row
                    self.title2zd_dict_COAF[article_title.upper()] = zd_number
                if dup_of not in ['', '-']:
                    self.zd2oa_dups_dict[zd_number] = dup_of

        return [
                self.apollo2zd_dict,
                self.doi2zd_dict,
                self.oa2zd_dict,
                self.title2zd_dict,
                self.title2zd_dict_COAF,
                self.title2zd_dict_RCUK,
                self.zd2oa_dups_dict,
                self.zd2zd_dict,
                self.zd_dict,
                self.zd_dict_COAF,
                self.zd_dict_RCUK,
                ]

    def plug_in_payment_data(self, cufs_export_type, paymentsfile, file_encoding = 'utf-8'):
        '''
        This function parses financial reports produced by CUFS. It tries to mach each payment in the CUFS report
        to a zd ticket and, if successful, it produces summations of payments per zd ticket and appends these
        values to zd_dict as output_apc_field and/or self.cufs_map.total_other

        :param cufs_export_type: type of report exported by CUFS. Supported values are 'RCUK' and 'COAF'
        :param paymentsfile: path of input CSV file containing payment data
        :param file_encoding: enconding of paymentsfile
        '''

        def calculate_balance(self, payments_dict, zd_number, payments_type):
            '''
            Sums a payment associated with a ZD number to the balance of payments already processed that were also
            associated with that number.

            :param payments_dict:
            :param zd_number:
            :param payments_type:
            :return:
            '''
            if payments_type == 'apc':
                balance_field = self.cufs_map.total_apc
            elif payments_type == 'other':
                balance_field = self.cufs_map.total_other
            existing_payment = payments_dict[zd_number]
            p_amount = float(existing_payment[balance_field].replace(',', ''))
            n_amount = float(row[self.cufs_map.amount_field].replace(',', ''))
            return existing_payment, str(p_amount + n_amount)

        def parse_apc_payments(self, zd_number, payments_dict_apc, row, row_counter, paymentsfile):
            '''
            Parses APC payments. Used twice by outer function.

            :param self:
            :param zd_number:
            :param payments_dict_apc:
            :param row:
            :param row_counter:
            :param paymentsfile:
            :return:
            '''
            if zd_number in payments_dict_apc.keys():
                # Another APC payment was already recorded for this ticket, so we concatenate values
                existing_payment, balance = calculate_balance(self, payments_dict_apc, zd_number, 'apc')
                for k in row.keys():
                    if (existing_payment[k] != row[k]) and \
                            (k not in [self.cufs_map.paydate_field]):  # DO NOT CONCATENATE PAYMENT DATES
                        n_value = existing_payment[k] + ' %&% ' + row[k]
                    else:
                        n_value = row[k]
                    payments_dict_apc[zd_number][k] = n_value
                payments_dict_apc[zd_number][self.cufs_map.total_apc] = balance
            else:
                payments_dict_apc[zd_number] = row
                payments_dict_apc[zd_number][self.cufs_map.total_apc] = \
                    payments_dict_apc[zd_number][self.cufs_map.amount_field]
            # Now that we dealt with the problem of several apc payments per ticket,
            # add payment info to master dict of zd numbers
            for field in payments_dict_apc[zd_number].keys():
                if (field in self.zd_dict[zd_number].keys()) and (row_counter == 0):
                    logging.warning('Dictionary for ZD ticket {} already contains a field named {}.'
                                    'It will be overwritten by the value in file {}.'.format(zd_number, field,
                                                                                             paymentsfile))
            self.zd_dict[zd_number].update(payments_dict_apc[zd_number])
            return payments_dict_apc

        if cufs_export_type == 'RCUK':
            self.cufs_map = cufs.RcukFieldsMapping()
        elif cufs_export_type == 'COAF':
            self.cufs_map = cufs.CoafFieldsMapping()
        else:
            sys.exit('{} is not supported.'.format(cufs_export_type))

        fileheader = extract_csv_header(paymentsfile)

        t_oa = re.compile("OA[ \-]?[0-9]{4,8}")
        t_zd = re.compile("ZD[ \-]?[0-9]{4,8}")
        payments_dict_apc = {}
        payments_dict_other = {}
        with open(paymentsfile, encoding=file_encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            row_counter = 0
            for row in reader:
                if row[self.cufs_map.oa_number] in cufs.oa_number_typos.keys():
                    row[self.cufs_map.oa_number] = cufs.oa_number_typos[row[self.cufs_map.oa_number]]
                m_oa = t_oa.search(row[self.cufs_map.oa_number].upper())
                m_zd = t_zd.search(row[self.cufs_map.oa_number].upper())
                zd_number = None
                if m_oa:
                    oa_number = m_oa.group().upper().replace("OA" , "OA-").replace(" ","")
                    try:
                        zd_number = manual_oa2zd_dict[oa_number] # might be obsolete; test
                    except KeyError:
                        try:
                            zd_number = self.oa2zd_dict[oa_number]
                        except KeyError:
                            logging.warning('A ZD number could not be found for {} in {}.' 
                                            'Data for this OA number will be ignored'.format(oa_number, paymentsfile))
                elif m_zd:
                    zd_number = m_zd.group().replace(" ","-").strip('ZDzd -')

                if row[self.cufs_map.invoice_field].strip() in cufs.invoice2zd_number.keys():
                    zd_number = cufs.invoice2zd_number[row[self.cufs_map.invoice_field]]

                if row[self.cufs_map.oa_number].strip() in cufs.description2zd_number.keys():
                    zd_number = cufs.description2zd_number[row[self.cufs_map.oa_number]]

                if zd_number:
                    if zd_number in cufs.zd_number_typos.keys():
                        zd_number = cufs.zd_number_typos[zd_number]
                    if cufs_export_type == 'RCUK':
                        if row[self.cufs_map.source_of_funds] == 'JUDB':
                            if row[self.cufs_map.transaction_code] == 'EBDU':
                                key = 'EBDU_' + str(row_counter)
                                self.parsed_payments[key] = row.copy()
                                payments_dict_apc = parse_apc_payments(self, zd_number, payments_dict_apc, row,
                                                                       row_counter, paymentsfile)
                            elif row[self.cufs_map.transaction_code] in ['EBDV', 'EBDW']:
                                key = 'EBDV-W_' + str(row_counter)
                                self.parsed_payments[key] = row.copy()
                                if zd_number in payments_dict_other.keys():
                                    # another page/membership payment was already recorded, so we concatenate values
                                    balance = calculate_balance(self, payments_dict_other, zd_number, 'other')
                                    for k in row.keys():
                                        if (existing_payment[k] != row[k]) and (k not in [self.cufs_map.paydate_field, self.cufs_map.transaction_code]):
                                            n_value = existing_payment[k] + ' %&% ' + row[k]
                                        elif k == self.cufs_map.transaction_code: #special treatment for this case necessary to avoid overwriting preexisting APC transaction code (EBDU); concatenate with value in apc dict
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
                                    payments_dict_other[zd_number][self.cufs_map.total_other] = balance
                                else:
                                    payments_dict_other[zd_number] = row
                                    payments_dict_other[zd_number][self.cufs_map.total_other] = \
                                        payments_dict_other[zd_number][self.cufs_map.amount_field]
                                    # Now that we dealt with the problem of several apc payments per ticket,
                                    # add payment info to master dict of zd numbers
                                for field in payments_dict_other[zd_number].keys():
                                    if (field in self.zd_dict[zd_number].keys()) and (row_counter == 0):
                                        logging.warning('Dictionary for ZD ticket {} already contains a field named {}.'
                                                        'It will be overwritten by the value in file {}.'.format(
                                            zd_number, field, paymentsfile))
                                self.zd_dict[zd_number].update(payments_dict_other[zd_number])
                            else:
                                # Not a EBDU, EBDV or EBDW payment
                                key = 'not_EBD*_payment_' + str(row_counter)
                                self.rejected_payments[key] = row
                                debug_filename = os.path.join(os.getcwd(), nonEBDU_payment_file_prefix + paymentsfile.split('/')[-1])
                                output_debug_csv(debug_filename, row, fileheader)
                        else:
                            ## NOT A JUDB PAYMENT
                            key = 'not_JUDB_payment_' + str(row_counter)
                            self.rejected_payments[key] = row
                            debug_filename = os.path.join(os.getcwd(), nonJUDB_payment_file_prefix + paymentsfile.split('/')[-1])
                            output_debug_csv(debug_filename, row, fileheader)
                    elif cufs_export_type == 'COAF':
                        key = 'no_transaction_field_' + str(row_counter)
                        self.parsed_payments[key] = row.copy()
                        payments_dict_apc = parse_apc_payments(self, zd_number, payments_dict_apc, row, row_counter,
                                                               paymentsfile)
                else:
                    # Payment could not be linked to a zendesk number
                    key = 'no_zd_match_' + str(row_counter)
                    self.rejected_payments[key] = row
                    debug_filename = os.path.join(os.getcwd(), unmatched_payment_file_prefix + paymentsfile.split('/')[-1])
                    output_debug_csv(debug_filename, row, fileheader)
                row_counter += 1