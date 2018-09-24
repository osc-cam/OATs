import datetime
import dateutil.parser
import os
import csv

DOI_CLEANUP = ['http://dx.doi.org/', 'https://doi.org/', 'http://dev.biologists.org/lookup/doi/', 'http://www.hindawi.com/journals/jdr/aip/2848759/']
DOI_FIX = {'0.1136/jmedgenet-2016-104295':'10.1136/jmedgenet-2016-104295'}

class oatslogger:

    def __init__(self, logfile):
        self.logfile = logfile

    def plog(self, *args, terminal=True):
        '''
        A function to print arguments to a log file
        :param args: the arguments to output
        :param terminal: if set to false, suppresses terminal output
        '''
        with open(self.logfile, 'a') as f:
            if terminal == True:
                print(' '.join(map(str, args)))
            for a in args:
                try:
                    f.write(str(a))
                    f.write(' ')
                except UnicodeEncodeError:
                    f.write('UnicodeEncodeError')
                    f.write(' ')
            f.write('\n')

def convert_date_str_to_yyyy_mm_dd(string, dateutil_options=None):
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
        return('')
    else:
        return(d)

def gen_chunks(reader, chunksize=100): # https://gist.github.com/miku/820490
    """
    Chunk generator. Take a CSV `reader` and yield
    `chunksize` sized slices.
    """
    chunk = []
    for index, line in enumerate(reader):
        if (index % chunksize == 0 and index > 0):
            yield chunk
            del chunk[:]
        chunk.append(line)
    yield chunk


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


def prune_and_cleanup_string(string, pruning_list, typo_dict=None):
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
    if typo_dict and (string in typo_dict.keys()):
        string = typo_dict[string]
    return(string.strip())


## function below currently used by invoice-fetcher; adapt that script to use zendesk.py module instead
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

def extract_csv_header(inputfile, enc = 'utf-8', delim = ','):
    '''
    This function returns a list of the fields contained in the header (first row) of
    a CSV file
    :param inputfile: path of CSV file
    :param enc: encoding of CSV file
    '''
    outputlist = []
    with open(inputfile, encoding = enc) as csvfile:
        headerreader = csv.reader(csvfile, delimiter=delim)
        #~ print(type(headerreader))
        for row in headerreader:
            outputlist.append(row)
    return(outputlist[0])

def output_debug_csv(outcsv, row_dict, csvheader = []):
    '''
    This function appends a row to an output CSV file
    :param outcsv: path of output CSV file
    :param row_dict: dictionary containing the row to be output
    :param csvheader: the header of the CSV file
    '''
    if not os.path.exists(outcsv):
        with open(outcsv, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csvheader)
            writer.writeheader()
    with open(outcsv, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csvheader)
        writer.writerow(row_dict)