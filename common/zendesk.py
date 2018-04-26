import csv
from oatsutils import prune_and_cleanup_string, DOI_CLEANUP, DOI_FIX

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
    dictionaries. Zendesk tickets with the 'Duplicate' field set to 'yes' are ignored.
    '''
    def __init__(self):
        self.apollo2zd_dict = {}
        self.doi2zd_dict = {}
        self.oa2zd_dict = {}
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
        with open(zenexport, encoding = "utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                zd_number = row[self.zd_fields.id]
                dup_of = row[self.zd_fields.duplicate_of]
                if (row[self.zd_fields.duplicate] in ['no', '-', '']) or (zd_number in manual_zendesk_duplicates_to_include):
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
                        if (doi in self.doi2zd_dict.keys()) and self.doi2zd_dict[doi]: ## Although we excluded tickets marked as duplicates from this loop, it is still possible to have unmarked duplicates reaching this line because of tickets that have not been processed yet by the OA team and/or errors
                            # print('zd_number:', zd_number)
                            # print('DOI:', doi)
                            # print('doi2zd_dict[doi]:', doi2zd_dict[doi])
                            # print('doi2zd_dict:', doi2zd_dict)
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
                else:
                    if dup_of not in ['', '-']:
                        self.zd2oa_dups_dict[zd_number] = dup_of
                    else:
                        pass # maybe capture these 'duplicates of empty string' somewhere

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