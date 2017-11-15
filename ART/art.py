#!/usr/bin/env python3
import os
import re
import csv
import datetime
try:
    import dateutil.parser
except ModuleNotFoundError:
    print('WARNING: Could not load the dateutil module. Please install it if you have admin rights. Conversion of dates will not work properly during this run')
import collections
from pprint import pprint
from difflib import SequenceMatcher

### SET UP WORKING FOLDER
home = os.path.expanduser("~")
working_folder = os.path.join(home, 'OATs', 'ART-wd')

DOI_CLEANUP = ['http://dx.doi.org/', 'https://doi.org/', 'http://dev.biologists.org/lookup/doi/', 'http://www.hindawi.com/journals/jdr/aip/2848759/']
DOI_FIX = {'0.1136/jmedgenet-2016-104295':'10.1136/jmedgenet-2016-104295'}
exclude_from_next_run_prefix = "ART_info_add_to_exclusion_list_because_not_in_funders_policy_"
logfile = os.path.join(working_folder, "ART_log.txt")
manual_title2zd_dict = {
    ###SPRINGER
    'Acute Posterior Cranial Fossa Hemorrhage—Is Surgical Decompression Better than Expectant Medical Management?' : '', ##NOT SUBMITTED TO APOLLO
    'Adipose tissue plasticity: how fat depots respond differently to pathophysiological cues' : '',
    'From Peak to Trough: Decline of the Algerian “Islamist Vote”' : '', ##NOT SUBMITTED TO APOLLO
    'Exoplanetary Atmospheres—Chemistry, Formation Conditions, and Habitability' : '', ##NOT SUBMITTED TO APOLLO
    '“Soft” policing at hot spots—do police community support officers work? A randomized controlled trial' : '16350',
    'Maternal Mind-Mindedness Provides a Buffer for Pre-Adolescents at Risk for Disruptive Behavior' : '', ##NOT SUBMITTED TO APOLLO
    'The aetiology of rickets-like lower limb deformities in Malawian children' : '', ##NOT SUBMITTED TO APOLLO
    'My friend Alan Mackay' : '', ##NOT SUBMITTED TO APOLLO
    'Non-equilibrium Steady States in Kac’s Model Coupled to a Thermostat' : '', ##NOT SUBMITTED TO APOLLO
    'Aligned carbon nanotube–epoxy composites: the effect of nanotube organization on strength, stiffness, and toughness' : '', ##NOT SUBMITTED TO APOLLO
    'Entity realism and singularist semirealism' : '', ##NOT SUBMITTED TO APOLLO
    'Neurosurgical Emergencies in Sports Neurology' : '', ##NOT SUBMITTED TO APOLLO
    'Free Energies and Fluctuations for the Unitary Brownian Motion' : '', ##NOT SUBMITTED TO APOLLO
    ##SPRINGER SIMILARITY MATCHES
    'Target templates specify visual, not semantic, features to guide search: A marked asymmetry between seeking and ignoring' : '15402',
    'Investigating upper urinary tract urothelial carcinomas: a single-centre 10-year experience' : '16400',
    'Report: increases in police use of force in the presence of body-worn cameras are driven by officer discretion: a protocol-based subgroup analysis of ten randomized experiments' : '16286',
    'Exploring Indus crop processing: combining phytolith and macrobotanical analyses to consider the organisation of agriculture in northwest India c. 3200–1500 <Emphasis Type="SmallCaps">bc</Emphasis>' : '16631',
    'On short time existence of Lagrangian mean curvature flow' : '16652',
    'Limit case analysis of the “stable indenter velocity” method for obtaining creep stress exponents from constant load indentation creep tests' : '17445',
    'Transcriptomic profiling of pancreatic alpha, beta and delta cell populations identifies delta cells as a principal target for ghrelin in mouse islets' : '17843',
    'Higher Spins from Nambu–Chern–Simons Theory' : '19874',
    'Unstable Mode Solutions to the Klein–Gordon Equation in Kerr-anti-de Sitter Spacetimes' : '38709',
    'An Association Between ICP-Derived Data and Outcome in TBI Patients: The Role of Sample Size' : '29290',
    ###WILEY
    'Refining Genotype-Phenotype Correlation in Alström Syndrome Through Study of Primary Human Fibroblasts' : '81394',
    'The canine POMC gene, obesity in Labrador retrievers and susceptibility to diabetes mellitus' : '39491',
    ##WILEY SIMILARITY MATCHES
    'From ?Virgin Births? to ?Octomom?: Representations of single motherhood via sperm donation in the UK media' : '30491',
    'Prognostic models for identifying adults with intellectual disabilities and mealtime support needs who are at greatest risk of respiratory infection and emergency hospitalization' : '74902',
    'Using predictions from a joint model for longitudinal and survival data to inform the optimal time of intervention in an abdominal aortic aneurysm screening programme' : '72229',
    'Markov models for ocular fixation locations in the pres- ence and absence of colour' : '69352',
    ###OUP
    'Changes over time in the health and functioning of older people moving into care homes: Analysis of data from the English Longitudinal Study of Ageing' : '76550',
    'Disease-free and overall survival at 3.5 years for neoadjuvant bevacizumab added to docetaxel followed by fluorouracil, epirubicin and cyclophosphamide, for women with HER2 negative early breast cancer: ARTemis Trial.' : '81145',
    'Cancer immunotherapy trial registrations increase exponentially but chronic immunosuppressive glucocorticoid therapy may compromise outcomes' : '81604',
    """Swinburneâ€™s <i>Atalanta In Calydon</i>: 
    Prosody as sublimation in Victorian â€˜Greekâ€™ tragedy""" : '18350',
    "Reading the Exeter Book Riddles as Life-Writing" : '63449'
    }

def similar(a, b):
    '''
    This function returns the ratio of similarity between 2 strings
    :param a: string 1
    :param b: string 2
    :return: ratio of similarity between strings
    '''
    return(SequenceMatcher(None, a, b).ratio())

def merge_csv_files(list_of_files, output_filename, repeated_header=1):
    '''
    This function merges CSV files
    :param list_of_files: a list of paths of CSV files
    :param output_filename: path of the merged CSV file
    :param repeated_header: whether or not input files contain a header
    '''
    fout=open(output_filename,"w")
    # first file:
    for line in open(list_of_files[0]):
        fout.write(line)
    # now the rest:    
    for num in list_of_files[1:]:
        f = open(num)
        if repeated_header == 1: #all files have a header
            included_lines = f.readlines()[1:] # skip the header
        elif repeated_header == 0: #files do not have a header, so we include all lines
            included_lines = f.readlines()
        
        for line in included_lines:
            fout.write(line)
        f.close() # not really needed
    fout.close()

def extract_csv_header(inputfile, enc = 'utf-8'):
    '''
    This function returns a list of the fields contained in the header (first row) of
    a CSV file
    :param inputfile: path of CSV file
    :param enc: encoding of CSV file
    '''
    outputlist = []
    with open(inputfile, encoding = enc) as csvfile:
        headerreader = csv.reader(csvfile)
        #~ print(type(headerreader))
        for row in headerreader:
            outputlist.append(row)
    return(outputlist[0])

def output_debug_info(outcsv, row_dict, csvheader = []):
    '''
    This function appends a row to an output CSV file
    :param outcsv: path of output CSV file
    :param row_dict: dictionary containing the row to be output
    :param csvheader: the header of the CSV file
    '''
    with open(outcsv, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csvheader)
        writer.writerow(row_dict)

rejected_rcuk_payment_dict = {}
included_rcuk_payment_dict = {}

def plug_in_payment_data(paymentsfile, fileheader, oa_number_field, output_apc_field, output_pagecolour_field, invoice_field = 'Ref 5', amount_field = 'Amount', file_encoding = 'charmap',transaction_code_field = 'Tran', source_funds_code_field = 'SOF', funder = 'RCUK'):
    '''
    This function parses financial reports produced by CUFS
    :param paymentsfile: path of input CSV file containing payment data
    :param fileheader: header of input CSV file
    :param oa_number_field: name of field in input file containing "OA-" numbers
    :param output_apc_field: name of field to output summed APC payments to
    :param output_pagecolour_field: name of field to output summed page/colour payments to
    :param invoice_field: name of field in input file containing invoice numbers
    :param amount_field: name of field in input file containing the amount of each payment
    :param file_encoding: enconding of input file
    :param transaction_code_field: name of field in input file containing the transaction code
                                    for APC payments (EBDU) or page/colour (EBDV)
    :param source_funds_code_field: name of field in input file containing the source of funds code (JUDB)
    :param funder: funder who requested this report (e.g. RCUK / COAF)
    '''
    #t_oa_zd = re.compile("(OA)?(ZD)?[ \-]?[0-9]{4,8}")
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
            #print('\n', 'oa_number_field:', oa_number_field)
            m_oa = t_oa.search(row[oa_number_field].upper())
            m_zd = t_zd.search(row[oa_number_field].upper())
            #before = row[oa_number_field]
            if m_oa:
                oa_number = m_oa.group().upper().replace("OA" , "OA-").replace(" ","")
                try:
                    zd_number = oa2zd_dict[oa_number]
                except KeyError:
                    ### MANUAL FIX FOR OLD TICKET
                    if oa_number == "OA-1128":
                        zd_number = '3743' #DOI: 10.1088/0953-2048/27/8/082001
                    else:
                        print("WARNING: A ZD number could not be found for", oa_number, "in", paymentsfile + ". Data for this OA number will NOT be exported.")
                        zd_number = ''
            elif m_zd:
                zd_number = m_zd.group().replace(" ","-").strip('ZDzd -')
            else:
                zd_number = ''
            
            if row[invoice_field].strip() in invoice2zd_number.keys():
                zd_number = invoice2zd_number[row[invoice_field]]
            
            if row[oa_number_field].strip() in description2zd_number.keys():
                zd_number = description2zd_number[row[oa_number_field]]
                
            if zd_number:
                if zd_number in zd_number_typos.keys():
                    zd_number = zd_number_typos[zd_number]
                #print('zd_number:', zd_number) 
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
                                p_amount = float(existing_payment[output_apc_field].replace(',' , ''))
                                n_amount = float(row[amount_field].replace(',' , ''))
                                balance = str(p_amount + n_amount)
                                for k in row.keys():
                                    if (existing_payment[k] != row[k]) and (k not in [rcuk_paydate_field, coaf_paydate_field]): #DO NOT CONCATENATE PAYMENT DATES
                                        n_value = existing_payment[k] + ' %&% ' + row[k]
                                    else:
                                        n_value = row[k]
                                    payments_dict_apc[zd_number][k] = n_value
                                payments_dict_apc[zd_number][output_apc_field] = balance
                            else:
                                ###STORE APC PAYMENT INFO INDEXED ON ZD NUMBER
                                payments_dict_apc[zd_number] = row
                                payments_dict_apc[zd_number][output_apc_field] = payments_dict_apc[zd_number][amount_field]
                            ### NOW THAT WE DEALT WITH THE PROBLEM OF SEVERAL APC PAYMENTS
                            ### FOR EACH ZD NUMBER, ADD PAYMENT INFO TO MASTER DICT 
                            ### OF ZD NUMBERS
                            for field in payments_dict_apc[zd_number].keys():
                                if (field in zd_dict[zd_number].keys()) and (row_counter == 0):
                                    print('WARNING: Dictionary for ZD ticket', zd_number, 'already contains a field named', field + '. It will be overwritten by the value in file', paymentsfile)
                            zd_dict[zd_number].update(payments_dict_apc[zd_number]) #http://stackoverflow.com/questions/8930915/append-dictionary-to-a-dictionary
                        elif row[transaction_code_field] in ['EBDV', 'EBDW']:
                            if funder == 'RCUK':
                                key = 'EBDV-W_' + str(row_counter)
                                included_rcuk_payment_dict[key] = row.copy()
                            if zd_number in payments_dict_other.keys():
                                ### ANOTHER PAGE/MEMBERSHIP PAYMENT WAS ALREADY RECORDED FOR THIS ZD 
                                ### NUMBER, SO WE CONCATENATE VALUES
                                existing_payment = payments_dict_other[zd_number]
                                p_amount = float(existing_payment[output_pagecolour_field].replace(',' , ''))
                                n_amount = float(row[amount_field].replace(',' , ''))
                                balance = str(p_amount + n_amount)
                                for k in row.keys():
                                    if (existing_payment[k] != row[k]) and (k not in [rcuk_paydate_field, coaf_paydate_field, transaction_code_field]):
                                        n_value = existing_payment[k] + ' %&% ' + row[k]
                                    elif k == transaction_code_field: #special treatment for this case necessary to avoid overwriting preexisting APC transaction code (EBDU); concatenate with value in apc dict
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
                                payments_dict_other[zd_number][output_pagecolour_field] = payments_dict_other[zd_number][amount_field]
                            ### NOW THAT WE DEALT WITH THE PROBLEM OF SEVERAL PAGE/MEMBERSHIP PAYMENTS
                            ### FOR EACH ZD NUMBER, ADD PAYMENT INFO TO MASTER DICT 
                            ### OF ZD NUMBERS
                            for field in payments_dict_other[zd_number].keys():
                                if (field in zd_dict[zd_number].keys()) and (row_counter == 0):
                                    print('WARNING: Dictionary for ZD ticket', zd_number, 'already contains a field named', field + '. It will be overwritten by the value in file', paymentsfile)
                            zd_dict[zd_number].update(payments_dict_other[zd_number]) #http://stackoverflow.com/questions/8930915/append-dictionary-to-a-dictionary
                        else:
                            ## NOT A EBDU, EBDV OR EBDW PAYMENT
                            key = 'not_EBD*_payment_' + str(row_counter)
                            if funder == 'RCUK':
                                rejected_rcuk_payment_dict[key] = row
                            debug_filename = nonEBDU_payment_file_prefix + paymentsfile.split('/')[-1]
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
                        p_amount = float(existing_payment[output_apc_field].replace(',' , ''))
                        n_amount = float(row[amount_field].replace(',' , ''))
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
                                print('WARNING: Dictionary for ZD ticket', zd_number, 'already contains a field named', field + '. It will be overwritten by the value in file', paymentsfile)
                    zd_dict[zd_number].update(payments_dict_apc[zd_number]) #http://stackoverflow.com/questions/8930915/append-dictionary-to-a-dictionary
            else:
                ## PAYMENT COULD NOT BE LINKED TO A ZENDESK NUMBER
                key = 'no_zd_match_' + str(row_counter)
                if funder == 'RCUK':
                    rejected_rcuk_payment_dict[key] = row
                debug_filename = os.path.join(working_folder, unmatched_payment_file_prefix, paymentsfile.split('/')[-1])
                output_debug_info(debug_filename, row, fileheader)
            row_counter += 1

def plug_in_metadata(metadata_file, matching_field, translation_dict, warning_message = '', file_encoding = 'utf-8'):
    '''
    This function appends data from various sources (Apollo, etc) to the dictionary
    produced from the zendesk export (zd_dict)
    :param metadata_file: input CSV file containing data from the new source
    :param matching_field: field to be used to match new data to zd_dict (e.g. doi, title, etc)
    :param translation_dict: dictionary to be used to match new data to a zendesk number
    :param warning_message: message to print if a match could not be found
    :param file_encoding: encoding of input file
    '''
    with open(metadata_file, encoding=file_encoding) as csvfile:
        reader = csv.DictReader(csvfile)
        row_counter = 0
        for row in reader:
            mf = row[matching_field]
            try:
                zd_number = translation_dict[mf]
            except KeyError:
                if warning_message:
                    print(warning_message)
                zd_number = ''
            
            if zd_number:
                for field in row.keys():
                    if (field in zd_dict[zd_number].keys()) and (row_counter == 0):
                        print('WARNING: Dictionary for ZD ticket', zd_number, 'already contains a field named', field + '. It will be overwritten by the value in file', metadata_file)
                zd_dict[zd_number].update(row)
            row_counter += 1

def process_repeated_fields(zd_list, report_field_list, ticket):
    '''
    This function populates fields in the output report that do NOT have a 1 to 1
    correspondence to zendesk data fields (e.g. Fund that APC is paid from (1)(2) and (3))
    :param zd_list: list of zendesk data fields that may be used to populate the output fields
    :param report_field_list: list of output report fields that should be populated with data from
                                fields in zd_list
    :param ticket:
    :return:
    '''
    #print('\n\n\n\n\n')
    #pprint(ticket)
    #print('\n')
    used_funders = []
    for fund_f in report_field_list: #e.g. Fund that APC is paid from (1)(2) and (3)
        #print('\n\n')
        #print('fund_f:', fund_f)
        for zd_f in zd_list: #'RCUK payment [flag]', 'COAF payment [flag]', etc
            #print('zd_list:', zd_list)
            #print('zd_f:', zd_f)
            #print('\n')
            if (fund_f not in report_dict[ticket].keys()) and (zd_f not in used_funders):
            ## 'Fund that APC is paid from 1, 2 or 3' NOT YET SET FOR THIS TICKET
                if '[flag]' in zd_f:
                    if report_dict[ticket][zd_f].strip().upper() == 'YES':
                        #print('zdfund2funderstr[zd_f]:', zdfund2funderstr[zd_f])
                        report_dict[ticket][fund_f] = zdfund2funderstr[zd_f]
                        used_funders.append(zd_f)
                else:
                    if not report_dict[ticket][zd_f].strip() == '-':
                        #print('report_dict[ticket][zd_f]:', report_dict[ticket][zd_f])
                        report_dict[ticket][fund_f] = report_dict[ticket][zd_f]
                        used_funders.append(zd_f)

def plog(*args, logfilename=logfile, terminal=False):
    '''
    A function to print arguments to a log file
    :param args: the argumes to output
    :param terminal:
    '''
    with open(logfilename, 'a') as f:
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
        return('')
    else:
        return(d)

def debug_export_excluded_records(excluded_debug_file, excluded_recs_logfile, excluded_recs):
    with open(excluded_debug_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
        writer.writeheader()
        for ticket in excluded_recs:
            writer.writerow(excluded_recs[ticket])
    with open(excluded_recs_logfile, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=allfieldnames, extrasaction='ignore')
        writer.writeheader()
        for ticket in excluded_recs:
            writer.writerow(excluded_recs[ticket])

def debug_export_excluded_records_prepayment(excluded_debug_file, excluded_recs, excluded_fieldnames):
    with open(excluded_debug_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=excluded_fieldnames, extrasaction='ignore')
        writer.writeheader()
        for ticket in excluded_recs:
            writer.writerow(excluded_recs[ticket])
            
def heuristic_match_by_title(title, publisher, title2zd_dict, policy_dict={}):
    '''
    A function to match publications to zendesk data based on similarity of title
    :param title:
    :param policy_dict:
    :param publisher:
    :return:
    '''
    unresolved_titles_sim = []
    possible_matches = []
    out_of_policy = []
    if policy_dict:
        for t in policy_dict.keys():
            #print('t:', t)
            similarity = similar(title.upper(), t)
            if similarity > 0.8:
                possible_matches.append((similarity, t))
        if len(possible_matches) > 0:
            possible_matches.sort(reverse=True)
            most_similar_title = possible_matches[0][1]
            zd_number = policy_dict[most_similar_title]
    #       print('\nWARNING: publisher record matched to ZD via similarity in title. Please review the matches carefully in the log file.\n')
            plog('Matched zd_no: ' + zd_number)
            plog('publisher title: ' + title + '\n')
            plog('ZD        title: ' + most_similar_title.lower() + '\n\n')
        else:
            for t in title2zd_dict.keys():
                #print('t:', t)
                similarity = similar(title.upper(), t)
                if similarity > 0.8:
                    possible_matches.append((similarity, t))
            if len(possible_matches) > 0:
                possible_matches.sort(reverse=True)
                most_similar_title = possible_matches[0][1]
                zd_number = title2zd_dict[most_similar_title]
                out_of_policy.append((title, zd_number))
                plog('Matched zd_no (OUT OF FUNDER POLICY): ' + zd_number)
                plog('publisher title: ' + title + '\n')
                plog('ZD        title: ' + most_similar_title.lower() + '\n\n')
            else:
                unresolved_titles_sim.append(title)
                print('\nWARNING:', publisher, 'record could not be matched to ZD:\n', title, '\n')
            zd_number = ''
        exclude_from_next_run = exclude_from_next_run_prefix + publisher.upper() + '.txt'
        with open(exclude_from_next_run, 'a') as f:
            for i in out_of_policy:
                f.write(i[0] + ', ')
    else:
        for t in title2zd_dict.keys():
            # print('t:', t)
            similarity = similar(title.upper(), t)
            if similarity > 0.8:
                possible_matches.append((similarity, t))
        if len(possible_matches) > 0:
            possible_matches.sort(reverse=True)
            most_similar_title = possible_matches[0][1]
            zd_number = title2zd_dict[most_similar_title]
            plog('Matched zd_no (OUT OF FUNDER POLICY): ' + zd_number)
            plog('publisher title: ' + title + '\n')
            plog('ZD        title: ' + most_similar_title.lower() + '\n\n')
        else:
            unresolved_titles_sim.append(title)
            print('\nWARNING:', publisher, 'record could not be matched to ZD:\n', title, '\n')
        zd_number = ''
    exclude_from_next_run = exclude_from_next_run_prefix + publisher.upper() + '.txt'
    with open(exclude_from_next_run, 'a') as f:
        for i in unresolved_titles_sim:
            f.write(i + '\n')
    return (zd_number)

def heuristic_match_by_title_original(title, policy_dict, publisher, title2zd_dict):
    '''
    A function to match publications to zendesk data based on similarity of title
    :param title:
    :param policy_dict:
    :param publisher:
    :return:
    '''
    unresolved_titles_sim = []
    possible_matches = []
    out_of_policy = []
    for t in policy_dict.keys():
        #print('t:', t)
        similarity = similar(title.upper(), t)
        if similarity > 0.8:
            possible_matches.append((similarity, t))
    if len(possible_matches) > 0:
        possible_matches.sort(reverse=True)
        most_similar_title = possible_matches[0][1]
        zd_number = policy_dict[most_similar_title]
#       print('\nWARNING: publisher record matched to ZD via similarity in title. Please review the matches carefully in the log file.\n')
        plog('Matched zd_no: ' + zd_number)
        plog('publisher title: ' + title + '\n')
        plog('ZD        title: ' + most_similar_title.lower() + '\n\n')
    else:
        for t in title2zd_dict.keys():
            #print('t:', t)
            similarity = similar(title.upper(), t)
            if similarity > 0.8:
                possible_matches.append((similarity, t))
        if len(possible_matches) > 0:
            possible_matches.sort(reverse=True)
            most_similar_title = possible_matches[0][1]
            zd_number = title2zd_dict[most_similar_title]
            out_of_policy.append((title, zd_number))
            plog('Matched zd_no (OUT OF FUNDER POLICY): ' + zd_number)
            plog('publisher title: ' + title + '\n')
            plog('ZD        title: ' + most_similar_title.lower() + '\n\n')
        else:
            unresolved_titles_sim.append(title)
            print('\nWARNING:', publisher, 'record could not be matched to ZD:\n', title, '\n')
        zd_number = ''
    exclude_from_next_run = exclude_from_next_run_prefix + publisher.upper() + '.txt'
    with open(exclude_from_next_run, 'a') as f:
        for i in out_of_policy:
            f.write(i[0] + ', ')
    return(zd_number)

def match_prepayment_deal_to_zd(doi, title, publisher, doi2zd_dict, doi2apollo, apollo2zd_dict, title2zd_dict, institution='University of Cambridge', restrict_to_rcuk_policy=True):
    '''
    This function attempts to match the DOI of a publication to zendesk data;
    if that fails, it calls a separate function to perform a match
    based on title similarity (heuristic_match_by_title)
    :param doi: a string containing the DOI of the publication
    :param title: a string containing the title of the publication
    :param publisher: a string containing the publisher of the publication
    :param doi2zd_dict: a dictionary translating DOIs to zendesk numbers
    :param doi2apollo: a dictionary translating DOIs to apollo handles
    :param apollo2zd_dict: a dictionary translating apollo handles to zendesk numbers
    :param institution: string containing the institution of the publication
    :return: tuple (zendesk_number, reason_zendesk_number_could_not_be_found)
    '''
    unresolved_dois = []
    unresolved_dois_apollo = []
    unresolved_titles = []
    unresolved_titles_sim = []
    if institution == 'University of Cambridge':
        if title.strip() in manual_title2zd_dict.keys():
            zd_number = manual_title2zd_dict[title.strip()]
            if not zd_number:
                return(('', 'Not in ZD'))
        else:
            try:
                zd_number = doi2zd_dict[doi]
            except KeyError:
                unresolved_dois.append(doi)
                try:
                    apollo_handle = doi2apollo[doi]
                    zd_number = apollo2zd_dict[apollo_handle]
                except KeyError:
                    unresolved_dois_apollo.append(doi)
                    try:
                        if restrict_to_rcuk_policy == True:
                            zd_number = title2zd_dict_RCUK[title.upper()]
                        else:
                            zd_number = title2zd_dict[title.upper()]
                    except KeyError:
                        unresolved_titles.append(title)
                        possible_matches = []
                        if restrict_to_rcuk_policy == True:
                            zd_number = heuristic_match_by_title(title, publisher, title2zd_dict, policy_dict=title2zd_dict_RCUK)
                        else:
                            zd_number = heuristic_match_by_title(title, publisher, title2zd_dict)
        #~ plog(str(len(unresolved_dois)) + ' DOIs in the ' + publisher + ' dataset could not be matched to ZD numbers:')
        #~ for doi in unresolved_dois:
            #~ plog(doi)
        #~ plog(str(len(unresolved_dois_apollo)) + ' DOIs in the ' + publisher + ' dataset could not be matched to ZD numbers via Apollo:')
        #~ for doi in unresolved_dois_apollo:
            #~ plog(doi)
        #~ plog(str(len(unresolved_titles)) + 'titles in the ' + publisher + ' dataset could not be matched to ZD numbers:')
        #~ for title in unresolved_titles:
            #~ plog(title + '\n')
        #~ plog(str(len(unresolved_titles_sim)) + 'titles in the ' + publisher + ' dataset could not be matched to ZD numbers with an acceptable degree of uncertainty:')
        #~ for title in unresolved_titles_sim:
            #~ plog(title, '\n')
    else:
        zd_number = ''
    return((zd_number, ''))

def import_prepayment_data_and_link_to_zd(inputfile, output_dict, rejection_dict, doi_field,
                                          title_field, filter_date_field, publisher, institution_field = '',
                                          field_renaming_list = [], dateutil_options='', exclude_titles = [],
                                          request_status_field='', delim=','): #field_renaming_list is a list of tuples in the form (<original field in inputfile>, <new name for field in inputfile to avoid conflict with fieldnames in zd_dict>)
    '''
    This function reads an input CSV file containing one publication per row. For each row,
    it attempts to match the publication to zendesk data based on doi (preferred) or
    similarity of publication title.
    :param inputfile: input CSV file containing publication data
    :param output_dict: an output dictionary containing all the matched data
    :param rejection_dict:
    :param doi_field: the column name of the DOI field in the input CSV file
    :param title_field: the column name of the title field in the input CSV file
    :param filter_date_field: the column name of the date field in the input CSV file that will be used
                            for filtering records (e.g. publication date; acceptance date, etc)
    :param publisher: name of the publisher that produced the input CSV file
    :param institution_field: the column name of the institution field in the input CSV file
    :param field_renaming_list:
    :param dateutil_options:
    :param exclude_titles: a list of titles of publications that should be excluded from the output
    :param request_status_field:
    :param delim: the delimiter of the csv file; defaults to comma
    :return:
    '''
    with open(inputfile) as csvfile:
        publisher_id = 1
        reader = csv.DictReader(csvfile, delimiter=delim)
        for row in reader:
            warning = 0
            manual_rejection = ''
            t = filter_prepayment_records(row, publisher, filter_date_field, request_status_field, dateutil_options)
            if t[0] == 1:
                doi = row[doi_field]
                title = row[title_field]
                if institution_field:
                    institution = row[institution_field]
                else:
                    institution = 'University of Cambridge'
                if not title.strip() in exclude_titles:
                    a = match_prepayment_deal_to_zd(doi, title, publisher, doi2zd_dict, doi2apollo, apollo2zd_dict, institution)
                    zd_number = a[0]
                    manual_rejection = a[1]
                else:
                    zd_number = ''
                    manual_rejection = 'Not covered by funder policy'
                #~ output_dict[publisher_id] = row
                for a in field_renaming_list:
                    #~ output_dict[publisher_id][a[1]] = output_dict[publisher_id][a[0]]
                    row[a[1]] = row[a[0]]
                    #~ del output_dict[publisher_id][a[0]]
                    del row[a[0]]
                if zd_number.strip():
                    #~ for fn in output_dict[publisher_id].keys():
                    for fn in row.keys():
                        try:
                            if fn in zd_dict[zd_number].keys():
                                print('WARNING:', fn, 'in output_dict will be overwritten by data in zd_dict')
                        except KeyError:
                            warning = 1
                if warning == 1:
                    print('WARNING:', zd_number, 'not in zd_dict. This is probably because the zd number for this article was obtained from manual_title2zd_dict rather than from zd_dict and either (1) the zd ticket is newer than the zd export used here (using a new export should solve the problem); or (2) this zd_number is a typo in manual_title2zd_dict')
                    zd_number = ''
                if zd_number:
                    if zd_number in included_in_report.keys():
                        print('WARNING: A report entry already exists for zd number:', zd_number)
                        print('TITLE:', title)
                        print('Please merge this duplicate in the exported report', '\n')
                    row.update(zd_dict[zd_number])
                    output_dict[publisher_id] = row
                else:
                    row[rejection_reason_field] = t[1] + manual_rejection
                    rejection_dict[publisher_id] = row
            else:
                row[rejection_reason_field] = t[1]
                rejection_dict[publisher_id] = row
            publisher_id += 1

def filter_prepayment_records(row, publisher, filter_date_field, request_status_field='', dateutil_options=''):
    prune = 0
    prune_reason = ''
    if publisher == 'Springer':
        #### THIS IS OBSOLETE BECAUSE SPRINGER NOW PROVIDES A REPORT
        #### FILTERED BY INSTITUTION BY DEFAULT
        # if row['Institution'].strip() in institution_filter:
        #     publication_date = row[filter_date_field]
        # else:
        #     prune = 1
        #     prune_reason = 'Other institution'
        publication_date = row[filter_date_field]
    elif (publisher == 'OUP') or (publisher == 'Wiley'):
        request_status = row[request_status_field]
        if request_status in ['Cancelled', 'Rejected', 'Denied']:
            prune = 1
            prune_reason = 'Rejected request'
        else:
            publication_date = row[filter_date_field]
            if publisher == 'Wiley':
                if not row['Deposits'].strip() == '': #EXCLUDE DEPOSITS FROM REPORT
                    prune = 1
                    prune_reason = 'Not an article (deposit)'
    else:
        print('WARNING: filter_prepayment_records does not know how to process publisher', publisher)
        prune = 1
        prune_reason = 'BUG: unknown publisher in filter_prepayment_records'
    if prune == 0:
        if dateutil_options:
            publication_date = dateutil.parser.parse(publication_date, dateutil_options)
        else:
            publication_date = dateutil.parser.parse(publication_date)
        if report_start_date <= publication_date <= report_end_date:
            return((1, prune_reason))
        else:
            prune_reason = 'Out of reporting period'
            return(0, prune_reason)
    else:
        return(0, prune_reason)

def match_datasource_fields_to_report_fields(datasource_dict, translation_dict, default_publisher = '', default_pubtype = '', default_deal = '', default_notes = ''):
    temp_dict = {}
    for ticket in datasource_dict:
        for rep_f in translation_dict:
            for zd_f in translation_dict[rep_f]:
                if (rep_f not in datasource_dict[ticket].keys()) and (zd_f in datasource_dict[ticket].keys()):
                    #print('datasource_dict[ticket][zd_f]:', datasource_dict[ticket][zd_f])
                    if datasource_dict[ticket][zd_f]: #avoids AttributeError due to NoneType objects
                        if not datasource_dict[ticket][zd_f].strip() in ['-', 'unknown']: #ZD uses "-" to indicate NA #cottagelabs uses "unknown" to indicate NA for licence 
                            datasource_dict[ticket][rep_f] = datasource_dict[ticket][zd_f]
                            #datasource_dict[ticket][rep_f] = datasource_dict[ticket][zd_f] + ' | ' + zd_f ##USE THIS IF YOU NEED TO FIND OUT WHERE EACH BIT OF INFO IS COMING FROM
        if default_publisher:
            datasource_dict[ticket]['Publisher'] = default_publisher
        if default_pubtype:
            datasource_dict[ticket]['Type of publication'] = default_pubtype
        if default_deal:
            datasource_dict[ticket]['Discounts, memberships & pre-payment agreements'] = default_deal
        if default_notes:
            datasource_dict[ticket]['Notes'] = default_notes
    return(datasource_dict)

def action_cleanup_debug_info():
    with open(os.path.join(working_folder, unmatched_payment_file_prefix, rcuk_paymentsfile), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rcuk_paymentsfieldnames)
        writer.writeheader()
    with open(os.path.join(working_folder, unmatched_payment_file_prefix, coaf_paymentsfile), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=coaffieldnames)
        writer.writeheader()
    with open(os.path.join(working_folder, nonJUDB_payment_file_prefix, rcuk_paymentsfile), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rcuk_paymentsfieldnames)
        writer.writeheader()
    with open(os.path.join(working_folder, nonEBDU_payment_file_prefix, rcuk_paymentsfile), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rcuk_paymentsfieldnames)
        writer.writeheader()

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

def action_index_zendesk_data():
    with open(zenexport, encoding = "utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            zd_number = row['Id']
            oa_number = row['externalID [txt]']
            article_title = row['Manuscript title [txt]']
            rcuk_payment = row['RCUK payment [flag]']
            rcuk_policy = row['RCUK policy [flag]']
    #        apc_payment = row['Is there an APC payment? [list]']
    #        green_version = 'Green allowed version [list]'
    #        embargo = 'Embargo duration [list]'
    #        green_licence = 'Green licence [list]',
            apollo_handle = row['Repository link [txt]'].replace('https://www.repository.cam.ac.uk/handle/' , '')
            doi = prune_and_cleanup_string(row['DOI (like 10.123/abc456) [txt]'], DOI_CLEANUP, DOI_FIX)
            row['DOI (like 10.123/abc456) [txt]'] = doi
            dateutil_options = dateutil.parser.parserinfo(dayfirst=True)
            publication_date = convert_date_str_to_yyyy_mm_dd(row['Publication date (YYYY-MM-DD) [txt]'], dateutil_options)
            row['Publication date (YYYY-MM-DD) [txt]'] = publication_date
            title2zd_dict[article_title.upper()] = zd_number
            doi2zd_dict[doi] = zd_number
            oa2zd_dict[oa_number] = zd_number
            apollo2zd_dict[apollo_handle] = zd_number
            zd2zd_dict[zd_number] = zd_number
            zd_dict[zd_number] = row
            if (rcuk_payment == 'yes') or (rcuk_policy) == 'yes':
                zd_dict_RCUK[zd_number] = row
                title2zd_dict_RCUK[article_title.upper()] = zd_number

def action_populate_doi2apollo(apolloexport, enc='utf-8'):
    '''
    This function takes a CSV file exported by Apollo and builds a dictionary
    translating DOIs to Apollo handles
    :param apolloexport: input CSV file
    :return: doi2apollo dictionary
    '''
    doi2apollo = {}
    with open(apolloexport, encoding = enc) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            apollo_handle = row['handle']
            if len(row['rioxxterms.versionofrecord'].strip()) > 5:
                doi = prune_and_cleanup_string(row['rioxxterms.versionofrecord'], DOI_CLEANUP, DOI_FIX)
            else:
                doi = prune_and_cleanup_string(row['dc.identifier.uri'].split(',')[0], DOI_CLEANUP, DOI_FIX)
            doi2apollo[doi] = apollo_handle
    return(doi2apollo)

def action_populate_report_dict():
    if paydate_field == rcuk_paydate_field:
        datetime_format_st = '%d-%b-%Y' #e.g 21-APR-2016
    elif paydate_field == coaf_paydate_field:
        datetime_format_st = '%d-%b-%y' #e.g 21-APR-16
    else:
        print('ERROR: unrecognised paydate_field', paydate_field)
    zd_dict_counter = 0
    for a in zd_dict:
        ## CHECK IF THERE IS A PAYMENT FROM REPORT REQUESTER; 
        ## IF THERE IS, ADD TO report_dict (I.E. INCLUDE IN REPORT)
        try:
            payments = zd_dict[a][paydate_field].split('%&%')
            for p in payments:
                payment_date = datetime.datetime.strptime(p.strip(), datetime_format_st)
                if report_start_date <= payment_date <= report_end_date:
                    report_dict[a] = zd_dict[a]
                else:
                    key = 'out_of_reporting_period_' + str(zd_dict_counter)
                    rejected_rcuk_payment_dict[key] = zd_dict[a]
        except KeyError:
            pass
            ## THIS WARNING IS NOT A GOOD IDEA BECAUSE MANY TICKETS OLDER THAN THE REPORTING PERIOD MATCH THIS CONDITION 
            #~ if zd_dict[a]['RCUK payment [flag]'] == 'yes':
                #~ print('WARNING: RCUK payment ticked in zendesk but no RCUK payment located for record:')
                #~ pprint(zd_dict[a])
                #~ print('\n')
        zd_dict_counter += 1

def action_export_payments_reconciliation():
    reconcile_prefix = 'ART_reconcile_'
    reconcile_file = os.path.join(working_folder, reconcile_prefix, rcuk_paymentsfile.split('/')[-1])
    reconcile_field = 'report_status'
    reconcile_fieldnames = rcuk_paymentsfieldnames + [reconcile_field]
    with open(reconcile_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=reconcile_fieldnames, extrasaction='ignore')
        writer.writeheader()
        for p in rejected_rcuk_payment_dict:
            rejected_rcuk_payment_dict[p][reconcile_field] = 'excluded'
            writer.writerow(rejected_rcuk_payment_dict[p])
        for p in included_rcuk_payment_dict:
            included_rcuk_payment_dict[p][reconcile_field] = 'included'
            writer.writerow(included_rcuk_payment_dict[p])

def action_populate_report_fields():
    rep_fund_field_list = ['Fund that APC is paid from (1)', 'Fund that APC is paid from (2)', 'Fund that APC is paid from (3)']

    zd_fund_field_list = ['RCUK payment [flag]', 'COAF payment [flag]', 'Other institution payment [flag]',
                          'Grant payment [flag]', 'Voucher/membership/offset payment [flag]',
                          'Author/department payment [flag]', 'Wellcome payment [flag]',
                          'Wellcome Supplement Payment [flag]']

    rep_funders = ['Funder of research (1)', 'Funder of research (2)', 'Funder of research (3)']
    zd_allfunders = [ 'ERC [flag]',
                      'Arthritis Research UK [flag]',
                      "Breast Cancer Now (Breast Cancer Campaign) [flag]", # used to be 'Breast Cancer Campaign [flag]',
                      "Parkinson's UK [flag]",
                      'ESRC [flag]', 'NERC [flag]', 'Bloodwise (Leukaemia & Lymphoma Research) [flag]',
                      'FP7 [flag]', 'NIHR [flag]', 'H2020 [flag]', 'AHRC [flag]', 'BBSRC [flag]', 'EPSRC [flag]',
                      'MRC [flag]', 'Gates Foundation [flag]', 'STFC [flag]', 'Cancer Research UK [flag]',
                      'Wellcome Trust [flag]', 'British Heart Foundation [flag]']

    rep_grants = ['Grant ID (1)', 'Grant ID (2)', 'Grant ID (3)']
    zd_grantfields = ['COAF Grant Numbers [txt]'] #ZD funders field could also be used, but it does not seem to be included in the default export; this could be because it is a "multi-line text field" 

    for ticket in report_dict:
        ##DEAL WITH THE EASY FIELDS FIRST (ONE TO ONE CORRESPONDENCE)
        for rep_f in rep2zd:
            for zd_f in rep2zd[rep_f]:
                if (rep_f not in report_dict[ticket].keys()) and (zd_f in report_dict[ticket].keys()):
                    if not report_dict[ticket][zd_f].strip( ) in ['-', 'unknown']: #ZD uses "-" to indicate NA #cottagelabs uses "unknown" to indicate NA for licence 
                        report_dict[ticket][rep_f] = report_dict[ticket][zd_f]
                        #report_dict[ticket][rep_f] = report_dict[ticket][zd_f] + ' | ' + zd_f ##USE THIS IF YOU NEED TO FIND OUT WHERE EACH BIT OF INFO IS COMING FROM
        ##THEN WITH THE CONDITIONAL FIELDS
        process_repeated_fields(zd_fund_field_list, rep_fund_field_list, ticket)
        process_repeated_fields(zd_allfunders, rep_funders, ticket)
        process_repeated_fields(zd_grantfields, rep_grants, ticket)

def action_adjust_total_apc_values():
    for a in report_dict:
        #print('\n\nTicket number:', a, '\n')
        #pprint(report_dict[a])
        total_apc_value = ''
        if (total_payamount_field in report_dict[a].keys()) and (total_of_payamount_field in report_dict[a].keys()):
            total_apc_value = float(report_dict[a][total_payamount_field].replace(',' , '').strip()) + float(report_dict[a][total_of_payamount_field].replace(',' , '').strip())
        elif total_payamount_field in report_dict[a].keys():
            total_apc_value = report_dict[a][total_payamount_field].replace(',' , '').strip()
        elif total_of_payamount_field in report_dict[a].keys():
            total_apc_value = report_dict[a][total_of_payamount_field].replace(',' , '').strip()
        report_dict[a][total_apc_field] = str(total_apc_value)
        
def action_manually_filter_and_export_to_report_csv():
    exclusion_list = [
    ('Article title', 'NAR Membership 2016'),
    ('Description', 'zd 13598'),
    ('APC paid (£) including VAT if charged', '0.0')#THESE CONSIST OF PAYMENTS THAT WERE REFUNDED (EITHER PAID BY ANOTHER FUNDER OR REFERRED TO A PREPAYMENT DEAL
    ]
    with open(outputfile, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
        writer.writeheader()
        for ticket in report_dict:
            exclude = 0
            for field, value in exclusion_list:
                #print('\n')
                #print(report_dict[ticket].keys())
                #print('APC:', zd_dict[a][field])
                #print(value)
                if (field in report_dict[ticket].keys()) and (str(report_dict[ticket][field]).strip() == value):
                 #   print('excluded')
                    exclude = 1
            #print(report_dict[ticket])
            if exclude == 0:
                writer.writerow(report_dict[ticket])
                included_in_report[ticket] = report_dict[ticket]
            else:
                excluded_recs[ticket] = report_dict[ticket]

#################################### VARIABLES ################################

###MANUAL FIXES FOR PAYMENT FILES
zd_number_typos = {'30878':'50878'}
oa_number_typos = {'OA 10768':'OA 10468'}
description2zd_number = {"OPEN ACCESS FOR R DERVAN'S ARTICLE 'ON K-STABILITY OF FINITE COVERS' IN THE LMS BULLETIN" : '16490', 'REV CHRG/ACQ TAX PD 04/16;  INV NO:Polymers-123512SUPPLIER:  MDPI AG' : '15589'}
invoice2zd_number = {'APC502145176':'48547', 'P09819649':'28975', 'Polymers-123512':'15589', 'Polymers-123512/BANKCHRG'
:'15589', '9474185' : '18153'}

lf = os.path.dirname(os.path.realpath(__file__))
os.chdir(lf)

reporttype = "COAF" #Report requester. Supported values are: RCUK or COAF
rcuk_paydate_field = 'Posted' #Name of field in rcuk_paymentsfile containing the payment date
rcuk_payamount_field = 'Amount' #Name of field in rcuk_paymentsfile containing the payment amount
total_rcuk_payamount_field = 'RCUK APC Amount' #Name of field we want the calculated total RCUK APC to be stored in
coaf_paydate_field = 'GL Posting Date' #Name of field in coaf_last_year and coaf_this_year containing the payment date
coaf_payamount_field = 'Burdened Cost' #Name of field in coaf_last_year and coaf_this_year containing the payment date
total_coaf_payamount_field = 'COAF APC Amount' #Name of field we want the calculated total COAF APC to be stored in
total_apc_field = 'Total APC amount'

if reporttype == "RCUK":
    paydate_field = rcuk_paydate_field
    payamount_field = rcuk_payamount_field
    total_payamount_field = total_rcuk_payamount_field
    other_funder = "COAF"
    of_payamount_field = coaf_payamount_field
    total_of_payamount_field = total_coaf_payamount_field
elif reporttype == "COAF":
    paydate_field = coaf_paydate_field
    payamount_field = coaf_payamount_field
    total_payamount_field = total_coaf_payamount_field
    other_funder = "RCUK"
    of_payamount_field = rcuk_payamount_field
    total_of_payamount_field = total_rcuk_payamount_field
else:
    print("ERROR: Could not determine report requester (RCUK or COAF)")
    raise

with open(logfile, 'w') as log:
    log.write('APC Reporting Tool log of last run\n')

doifile = os.path.join(working_folder, "DOIs_for_cottagelabs.csv")
outputfile = os.path.join(working_folder, "COAF_report_draft.csv")
excluded_recs_logfile = os.path.join(working_folder, "COAF_report_excluded_records.csv")
rcuk_veje = os.path.join(working_folder, "VEJE_2017-10-31.csv")
rcuk_veji = os.path.join(working_folder, "VEJI_2017-10-31.csv")
rcuk_vejj = os.path.join(working_folder, "VEJJ_2017-10-31.csv")
rcuk_paymentsfile = os.path.join(working_folder, "RCUK_merged_payments_file.csv")
merge_csv_files([rcuk_veje, rcuk_veji, rcuk_vejj], rcuk_paymentsfile)
# coaf_last_year = os.path.join(working_folder, 'veag45.csv')
# coaf_this_year = os.path.join(working_folder, 'veag50.csv')
coaf_paymentsfile = os.path.join(working_folder, "VEAG050_2017-10-31.csv")
# merge_csv_files([coaf_last_year, coaf_this_year], coaf_paymentsfile)
zenexport = os.path.join(working_folder, "export-2017-11-09-2150-5703871969.csv")
zendatefields = os.path.join(working_folder, "rcuk-report-active-date-fields-for-export-view-2017-11-13-2307.csv")
apolloexport = os.path.join(working_folder, "Apollo_all_items-20171110.csv")
cottagelabsexport = "DOIs_for_cottagelabs_edited_results.csv"
# springercompact_last_year = "Springer_Compact-December_2016_Springer_Compact_Report_for_UK_Institutions.csv"
# springercompact_this_year = "Springer_Compact-March_2017_Springer_Compact_Report_for_UK_Institutions.csv"
springercompactexport = os.path.join(working_folder, "article_approval_2016-01-01_to_2017-11-10.csv")
# merge_csv_files([springercompact_last_year, springercompact_this_year], springercompactexport)
wileyrcukcoaf = os.path.join(working_folder, "Wiley_RCUK_COAF_ArticleHistoryReport.csv")
wileycredit = os.path.join(working_folder, "Wiley_CREDIT_ArticleHistoryReport.csv")
wileyexport = os.path.join(working_folder, "Wiley_all_accounts.csv")
merge_csv_files([wileyrcukcoaf, wileycredit], wileyexport)
oupexport = os.path.join(working_folder, "OUP OA Charge Data.csv")
report_template = os.path.join(working_folder, "Jisc_template_v4.csv")
report_start_date = datetime.datetime(2016, 10, 1)
report_end_date = datetime.datetime(2017, 9, 30)
green_start_date = datetime.datetime(2016, 1, 1)#Using 1 Jan 2016 to 31 Dec 2016 for green compliance estimate to match WoS period
green_end_date = datetime.datetime(2016, 12, 31, hour = 23, minute = 59, second = 59)

unmatched_payment_file_prefix = 'ART_debug_payments_not_matched_to_zd_numbers__'
nonJUDB_payment_file_prefix = 'ART_debug_non_JUDB_payments__'
nonEBDU_payment_file_prefix = 'ART_debug_non_EBDU_EBDV_or_EBDW_payments__'

###MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS IN zd_dict
rep2zd = [
('Date of acceptance', ['Symplectic acceptance date (YYYY-MM-DD) [txt]', 'Acceptance date', 'dcterms.dateAccepted']),
('PubMed ID', ['PMID']), #from cottagelabs
('DOI', ['DOI (like 10.123/abc456) [txt]', 'rioxxterms.versionofrecord', 'dc.identifier.uri']), #dc.identifier.uri often contains DOIs that are not in rioxxterms.versionofrecord, but it needs cleaning up (e.g. http://dx.doi.org/10.1111/oik.02622,https://www.repository.cam.ac.uk/handle/1810/254674 ); use only if the DOI cannot be found elsewhere
('Publisher', ['Publisher [txt]', 'dc.publisher']),
('Journal', ['Journal title [txt]', 'prism.publicationName']),
('E-ISSN', ['ISSN']), #from cottagelabs
('Type of publication', ['Symplectic item type [txt]', 'dc.type']),
('Article title', ['Manuscript title [txt]', 'dc.title']),
('Date of publication', ['Publication date (YYYY-MM-DD) [txt]', 'dc.date.issued']),
('Date of APC payment', [paydate_field]),
#('APC paid (actual currency) excluding VAT', NA ##COULD PROBABLY OBTAIN FROM CUFS IF REALLY NECESSARY
#('Currency of APC', NA ##COULD PROBABLY OBTAIN FROM CUFS IF REALLY NECESSARY
('APC paid (£) including VAT if charged', [total_apc_field]), ##CALCULATED FROM 'Amount'
('Additional publication costs (£)', ['Page, colour or membership amount']), ##CALCULATED FROM 'Amount'
 #('Discounts, memberships & pre-payment agreements',
('Amount of APC charged to COAF grant (including VAT if charged) in £', [total_coaf_payamount_field]),
('Amount of APC charged to RCUK OA fund (including VAT if charged) in £', [total_rcuk_payamount_field]),
('Licence', ['EPMC Licence', 'Publisher Licence', 'Licence applied by publisher [list]'])
 #('Notes'
]
rep2zd = collections.OrderedDict(rep2zd)

doi2zd_dict = {} #Dictionary mapping DOI to zd number
apollo2zd_dict = {} #Dictionary mapping apollo handle to zd number
oa2zd_dict = {} #Dictionary mapping OA number to zd number
zd2zd_dict = {} #Dictionary mapping zd number to zd number, so that we can use general function plug_in_metadata to match a zd export to another zd export
title2zd_dict = {} #Dictionary mapping article title to zd number
zd_dict = {}
zd_dict_RCUK = {} #A dictionary of tickets that have either RCUK policy or RCUK payment ticked. Needed for title matching because of the SE duplicates, which have an article title, but no decision
title2zd_dict_RCUK = {}
doi2apollo = {} #Dictionary mapping doi to handle (created using data from apollo export)

zdfund2funderstr = {
    'RCUK payment [flag]' : 'RCUK',
    'COAF payment [flag]' : 'COAF',
    'Other institution payment [flag]' : 'ERROR: OTHER INSTITUTION',
    'Grant payment [flag]' : 'Institutional',
    'Voucher/membership/offset payment [flag]' : 'Institutional',
    'Author/department payment [flag]' : 'Institutional',
    'Wellcome payment [flag]' : 'Wellcome Trust',
    'Wellcome Supplement Payment [flag]' : 'Wellcome Trust',
    'ERC [flag]' : 'ERC',
    'Arthritis Research UK [flag]' : 'Arthritis Research UK',
    'Breast Cancer Campaign [flag]' : 'Breast Cancer Campaign',
    "Parkinson's UK [flag]" : "Parkinson's UK",
    'ESRC [flag]' : 'ESRC',
    'NERC [flag]' : 'NERC' ,
    'Bloodwise (Leukaemia & Lymphoma Research) [flag]' : 'Bloodwise',
    'FP7 [flag]' : 'FP7',
    'NIHR [flag]' : 'NIHR',
    'H2020 [flag]' : 'H2020',
    'AHRC [flag]' : 'AHRC',
    'BBSRC [flag]' : 'BBSRC',
    'EPSRC [flag]' : 'EPSRC',
    'MRC [flag]' : 'MRC',
    'Gates Foundation [flag]' : 'Bill and Melinda Gates Foundation',
    'STFC [flag]' : 'STFC',
    'Cancer Research UK [flag]' : 'Cancer Research UK',
    'Wellcome Trust [flag]' : 'Wellcome Trust',
    'British Heart Foundation [flag]': 'British Heart Foundation'
    }

if __name__ == '__main__':


    ############################ACTION STARTS HERE##################################

    #~ tempfieldnames = extract_csv_header(zenexport)
    #~ pprint(tempfieldnames)
    #~ raise

    zendeskfieldnames = extract_csv_header(zenexport, "utf-8")
    zendatefieldnames = extract_csv_header(zendatefields, "utf-8")
    rcuk_paymentsfieldnames = extract_csv_header(rcuk_paymentsfile, "utf-8")
    coaffieldnames = extract_csv_header(coaf_paymentsfile, "utf-8")
    apollofieldnames = extract_csv_header(apolloexport, "utf-8")
    # cottagelabsfieldnames = extract_csv_header(cottagelabsexport, "utf-8")
    springerfieldnames = extract_csv_header(springercompactexport, "utf-8")
    wileyfieldnames = extract_csv_header(wileyrcukcoaf, "utf-8")
    oupfieldnames = extract_csv_header(oupexport, "utf-8")
    rejection_reason_field = 'Reason for exclusion'

    allfieldnames = zendeskfieldnames + zendatefieldnames + rcuk_paymentsfieldnames + apollofieldnames + coaffieldnames
    # allfieldnames += cottagelabsfieldnames + springerfieldnames + wileyfieldnames + oupfieldnames


    #~ #pprint(allfieldnames)
    #~ #raise

    #~ ##CLEANUP DEBUG INFO FROM PREVIOUS RUNS BY WRITING HEADERS
    #~ print('STATUS: cleanning up debug info from previous run')
    #~ action_cleanup_debug_info()

    # ###INDEX INFO FROM ZENDESK ON ZD NUMBER
    # plog('STATUS: indexing zendesk info on zd number', terminal=True)
    # action_index_zendesk_data()
    #
    # ### POPULATE doi2apollo DICTIONARY
    # plog('STATUS: populating doi2apollo dictionary', terminal=True)
    # action_populate_doi2apollo(apolloexport)
    #
    # #### PLUGGING IN DATA FROM ZENDESK DATE FIELDS
    # plog('STATUS: plugging in data from zendesk date fields into zd_dict', terminal=True)
    # plug_in_metadata(zendatefields, 'id', zd2zd_dict)
    #
    # # #### ESTIMATE COMPLIANCE VIA GREEN ROUTE
    # # plog('STATUS: estimating compliance via the green route', terminal=True)
    # # ### TAKE A SAMPLE OF OUTPUTS COVERED BY THE RCUK POLICY AND PUBLISHED DURING THE REPORTING PERIOD
    # # ### EXCLUDE ZD TICKETS MARKED AS DUPLICATES OR "WRONG VERSION"
    # # rcuk_dict = {}
    # # for a in zd_dict:
    # #     row = zd_dict[a]
    # #     rcuk_policy = row['RCUK policy [flag]']
    # #     ticket_creation = dateutil.parser.parse(row['Created at'])
    # #     wrong_version = row['Wrong version [flag]']
    # #     dup = row['Duplicate [flag]']
    # #     #~ if not row['Online Publication Date (YYYY-MM-DD) [txt]'] == '-':
    # #         #~ try:
    # #             #~ publication_date = dateutil.parser.parse(row['Online Publication Date (YYYY-MM-DD) [txt]'].replace('--','-'))
    # #         #~ except ValueError:
    # #             #~ print(row['Online Publication Date (YYYY-MM-DD) [txt]'])
    # #             #~ raise
    # #     #~ else:
    # #         #~ try:
    # #             #~ if not row['Publication Date (YYYY-MM-DD) [txt]'] == '-':
    # #                 #~ publication_date = dateutil.parser.parse(row['Publication Date (YYYY-MM-DD) [txt]'])
    # #             #~ else:
    # #                 #~ publication_date = datetime.datetime(2100, 1, 1)
    # #         #~ except KeyError:
    # #             #~ publication_date = datetime.datetime(2100, 1, 1)
    # #     if (rcuk_policy == 'yes') and (wrong_version != 'yes') and (dup != 'yes') and (green_start_date <= ticket_creation <= green_end_date):
    # #         rcuk_dict[a] = zd_dict[a]
    # #
    # # ## CHECK HOW MANY OF THOSE ARE GOLD, GREEN OR UNKNOWN
    # # green_dict = {}
    # # gold_dict = {}
    # # green_counter = 0
    # # gold_counter = 0
    # # apc_payment_values = ['Yes', 'Wiley Dashboard', 'OUP Prepayment Account', 'Springer Compact']
    # # WoS_total = 2400 #From Web of Science: number of University of Cambridge publications (articles, reviews and proceeding papers) acknowledging RCUK funding during the green reporting period
    # # for a in rcuk_dict:
    # #     row = rcuk_dict[a]
    # #     apc_payment = row['Is there an APC payment? [list]']
    # #     green_version = row['Green allowed version [list]']
    # #     embargo = row['Embargo duration [list]']
    # #     green_licence = row['Green licence [list]']
    # #     if apc_payment in apc_payment_values:
    # #         gold_counter += 1
    # #         gold_dict[a] = rcuk_dict[a]
    # #     else:
    # #         green_counter += 1
    # #         green_dict[a] = rcuk_dict[a]
    # #
    # # rcuk_papers_total = gold_counter + green_counter
    # #
    # # plog('RESULT --- COMPLIANCE VIA GREEN/GOLD ROUTES:', terminal = True)
    # # plog(str(rcuk_papers_total), 'ZD tickets covered by the RCUK open access policy were created during the green reporting period, of which:', terminal=True)
    # # plog(str(gold_counter), '(' + str(gold_counter / rcuk_papers_total) + ') tickets were placed in the GOLD route to comply with the policy', terminal=True)
    # # plog(str(green_counter), '(' + str(green_counter / rcuk_papers_total) + ') tickets were placed in the GREEN route to comply with the policy', terminal=True)
    # # plog('RESULT --- COMPLIANCE VIA GREEN/GOLD ROUTES AS A RATIO OF WoS TOTAL:', terminal = True)
    # # plog(str(WoS_total), 'papers (articles, reviews and proceedings papers) acknowledging RCUK funding were published by the University of Cambridge during the green reporting period, of which:', terminal=True)
    # # plog(str(gold_counter / WoS_total), 'complied via the GOLD route', terminal = True)
    # # plog(str(green_counter / WoS_total), 'complied via the GREEN route', terminal = True)
    # #
    # # #~ raise
    #
    # #### PLUGGING IN DATA FROM THE RCUK AND COAF PAYMENTS SPREADSHEETS
    # plug_in_payment_data(rcuk_paymentsfile, rcuk_paymentsfieldnames, 'Description', total_rcuk_payamount_field, 'Page, colour or membership amount', amount_field = rcuk_payamount_field, file_encoding = 'utf-8', transaction_code_field = 'Tran', funder = 'RCUK')
    # plug_in_payment_data(coaf_paymentsfile, coaffieldnames, 'Comment', total_coaf_payamount_field, 'COAF Page, colour or membership amount', invoice_field = 'Invoice', amount_field = coaf_payamount_field, file_encoding = 'utf-8', funder = 'COAF')
    #
    # #### PLUGGING IN DATA FROM APOLLO
    # ###NEED TO MAP THIS DATA USING REPOSITORY HANDLE, BECAUSE APOLLO DOES
    # ###NOT STORE ZD AND OA NUMBERS FOR ALL SUBMISSIONS
    # plug_in_metadata(apolloexport, 'handle', apollo2zd_dict)
    #
    # #### PLUGGING IN DATA FROM COTTAGELABS
    # try:
    #     plug_in_metadata(cottagelabsexport, 'DOI', doi2zd_dict)
    # except FileNotFoundError:
    #     plog('WARNING: Compliance data from Cottage Labs not found; I will assume this is because it was not generated yet',
    #          terminal=True)
    #
    # #### MAUALLY FIX SOME PROBLEMS
    # zd_dict['3743']['DOI'] = '10.1088/0953-2048/27/8/082001'
    # zd_dict['3743']['externalID [txt]'] = 'OA-1128'
    # zd_dict['3743']['Date of acceptance'] = '2014-06-11'
    # zd_dict['3743']['Publisher'] = 'IOP'
    # zd_dict['3743']['Journal'] = 'Superconductor Science and Technology'
    # zd_dict['3743']['Type of publication'] = 'Article'
    # zd_dict['3743']['Article title'] = 'A Trapped Field of 17.6 T in Melt-Processed, Bulk Gd-Ba-Cu-O Reinforced with Shrink-Fit Steel'
    # zd_dict['3743']['Date of publication'] = '2014-06-25'
    # zd_dict['3743']['Fund that APC is paid from (1)'] = 'RCUK'
    # zd_dict['3743']['Funder of research (1)'] = 'EPSRC'
    # zd_dict['3743']['Grant ID (1)'] = 'EP/K02910X/1'
    # zd_dict['3743']['Licence'] = 'CC BY'
    #
    # #### NOW THAT WE PLUGGED IN ALL DATA SOURCES INTO THE ZENDESK EXPORT,
    # #### PRODUCE THE FIRST PART OF THE REPORT (PAYMENTS LINKED TO ZENDESK)
    # report_dict = {}
    # ### START BY FILTERING WHAT WE NEED
    # action_populate_report_dict()
    #
    # #### EXPORT PAYMENTS IN ORIGINAL FORMAT WITH AN EXTRA COLUMN "INCLUDED/EXCLUDED FROM REPORT" FOR RECONCILIATION/DEBUGGING:
    # action_export_payments_reconciliation()
    #
    # #### NOW ADJUST TOTAL APC VALUES FOR TICKETS WHERE THE APC WAS SPLIT BETWEEN
    # #### RCUK AND COAF
    # action_adjust_total_apc_values()
    #
    # ### POPULATE REPORT FIELDS WITH DATA FROM ZD/APOLLO/PAYMENT FIELDS
    # ### CONVERT DATA WHEN NEEDED
    # action_populate_report_fields()
    #
    # excluded_recs = {}
    # included_in_report = {}
    #
    # report_fields = extract_csv_header(report_template, "utf-8")
    # custom_rep_fields = ['id', 'externalID [txt]', 'Reason for exclusion', 'Description', 'Ref 1', 'Ref 5', 'RCUK policy [flag]', 'RCUK payment [flag]', 'COAF policy [flag]', 'COAF payment [flag]', 'handle']
    # report_fieldnames = report_fields + custom_rep_fields + rcuk_paymentsfieldnames
    # #report_fieldnames = report_fields
    #
    # ### THEN EXPORT THE INCLUDED TICKETS TO THE REPORT CSV
    # action_manually_filter_and_export_to_report_csv()
    #
    # ### EXPORT EXCLUDED RECORDS TO CSVs
    # excluded_debug_file = 'ART_debug_payments_matched_to_zd_tickets_excluded_from_report.csv'
    # debug_export_excluded_records(excluded_debug_file, excluded_recs_logfile, excluded_recs)

    #### ADD DATA FROM PUBLISHER DEALS TO THE END OF THE REPORT
    institution_filter = ['University of Cambridge']

    ### SPRINGER
    ### MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS
    rep2springer = [
    ('Date of acceptance', ['Acceptance Date']),
    #('PubMed ID', #NA
    ('DOI', ['DOI']),
    #('Publisher', #NOT A VARIABLE; DEFAULT TO SPRINGER
    ('Journal', ['Journal Title']),
    ('E-ISSN', ['eISSN']),
    #('Type of publication', #NOT A VARIABLE; DEFAULT TO ARTICLE
    ('Article title', ['Article Title']),
    ('Date of publication', ['Online Publication Date']),
    #('Date of APC payment', #NA
    ('APC paid (actual currency) excluding VAT', ['Journal APC']),
    #('Currency of APC', #NA
    #('APC paid (£) including VAT if charged', #NA
    #('Additional publication costs (£)', #NA
    #('Discounts, memberships & pre-payment agreements', #NOT A VARIABLE; DEFAULT TO SPRINGER COMPACT?
    #('Amount of APC charged to COAF grant (including VAT if charged) in £', #NA
    #('Amount of APC charged to RCUK OA fund (including VAT if charged) in £', #NA
    ('Licence', ['License Type']),
    ('Notes', ['Comments'])
    ]
    rep2springer = collections.OrderedDict(rep2springer)

    springer_dict = {}
    rejection_dict_springer = {}
    dateutil_springer = dateutil.parser.parserinfo(dayfirst=True)
    exclude_titles_springer = ['Clinical Trials in Vasculitis', 'PET Imaging of Atherosclerotic Disease: Advancing Plaque Assessment from Anatomy to Pathophysiology', 'Consequences of tidal interaction between disks and orbiting protoplanets for the evolution of multi-planet systems with architecture resembling that of Kepler 444', 'Hunter-Gatherers and the Origins of Religion', 'A 2-adic automorphy lifting theorem for unitary groups over CM fields', 'Basal insulin delivery reduction for exercise in type 1 diabetes: finding the sweet spot', 'Hohfeldian Infinities: Why Not to Worry', 'Ultrastructural and immunocytochemical evidence for the reorganisation of the milk fat globule membrane after secretion', 'Data processing for the sandwiched Rényi divergence: a condition for equality', 'Knowledge, beliefs and pedagogy: how the nature of science should inform the aims of science education (and not just when teaching evolution)', 'Gender patterns in academic entrepreneurship']
    import_prepayment_data_and_link_to_zd(springercompactexport, springer_dict, rejection_dict_springer,
                                          'DOI', 'article title', # this used to be 'Article Title' in Springer Compact reports,
                                          'approval requested date', # 'Online Publication Date' was previously used, but it was renamed to 'online first publication date' and has blank values for several articles
                                          'Springer',
                                          'membership institute', # this used to be 'Institution',
                                          dateutil_options=dateutil_springer,
                                          exclude_titles=exclude_titles_springer,
                                          delim=';')

    excluded_debug_file = 'ART_debug_Springer_Compact_rejected_records.csv'
    springer_reject_fieldnames = [rejection_reason_field]
    for a in springerfieldnames:
        springer_reject_fieldnames.append(a)
    #pprint(rejection_dict_springer)
    debug_export_excluded_records_prepayment(excluded_debug_file, rejection_dict_springer, springer_reject_fieldnames)

    springer_out_dict = match_datasource_fields_to_report_fields(springer_dict, rep2springer, 'Springer', 'Article', 'Springer Compact', 'Springer Compact')

    report_fieldnames += ['Is there an APC payment? [list]']
    with open(outputfile, 'a') as csvfile: #APPEND TO THE SAME OUTPUTFILE
        writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
        #~ writer.writeheader()
        for doi in springer_out_dict:
            publication_date = springer_out_dict[doi]['Date of publication']
            publication_date = dateutil.parser.parse(publication_date, dateutil_springer)
            springer_out_dict[doi]['Date of publication'] = publication_date.strftime('%Y-%m-%d')
            if 'Date of acceptance' in springer_out_dict[doi].keys():
                acceptance_date = dateutil.parser.parse(springer_out_dict[doi]['Date of acceptance'], dateutil_springer)
                springer_out_dict[doi]['Date of acceptance'] = acceptance_date.strftime('%Y-%m-%d')
            writer.writerow(springer_out_dict[doi])

    print('STATUS: Finished processing Springer Compact entries')

    ### WILEY
    ###MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS
    rep2wiley = [
    ('Date of acceptance', ['Article Accepted Date']),
    #('PubMed ID', #NA
    ('DOI', ['DOI']),
    ('Publisher', ['Publisher']),
    ('Journal', ['Journal']),
    #('E-ISSN', ['eISSN']), #NA
    ('Type of publication', ['Article Type']),
    ('Article title', ['Article Title']),
    #('Date of publication', ['Online Publication Date']), #NA
    #('Date of APC payment', #NA
    ('APC paid (actual currency) excluding VAT', ['Full APC']),
    #('Currency of APC', #NA
    #('APC paid (£) including VAT if charged', #NA
    #('Additional publication costs (£)', #NA
    #('Discounts, memberships & pre-payment agreements', #NOT A VARIABLE; DEFAULT TO OTHER?
    #('Amount of APC charged to COAF grant (including VAT if charged) in £', #NA
    #('Amount of APC charged to RCUK OA fund (including VAT if charged) in £', #NA
    ('Licence', ['License Type']),
    #('Notes', ['Comments']) #DEFAULT TO "WILEY PREPAYMENT DEAL | Discount:" + 'Discount'
    ]
    rep2wiley = collections.OrderedDict(rep2wiley)

    wiley_dict = {}
    rejection_dict_wiley = {}
    dateutil_wiley = dateutil.parser.parserinfo(dayfirst=True)
    filter_date_field_wiley = 'Date'
    request_status_field_wiley = 'Request Status'
    exclude_titles_wiley = ['Chromatin determinants impart camptothecin sensitivity']
    import_prepayment_data_and_link_to_zd(wileyexport, wiley_dict, rejection_dict_wiley, 'DOI', 'Article Title', filter_date_field_wiley, 'Wiley', field_renaming_list = [('Journal Type', 'Wiley Journal Type'), ('DOI', 'Wiley DOI'), ('Publisher', 'Wiley Publisher')], dateutil_options=dateutil_wiley, exclude_titles=exclude_titles_wiley, request_status_field=request_status_field_wiley) #field_renaming_list is a list of tuples in the form (<original field in inputfile>, <new name for field in inputfile to avoid conflict with fieldnames in zd_dict>)

    excluded_debug_file = 'ART_debug_Wiley_Dashboard_rejected_records.csv'
    wiley_reject_fieldnames = [rejection_reason_field]
    for a in wileyfieldnames:
        wiley_reject_fieldnames.append(a)
    debug_export_excluded_records_prepayment(excluded_debug_file, rejection_dict_wiley, wiley_reject_fieldnames)

    wiley_out_dict = match_datasource_fields_to_report_fields(wiley_dict, rep2wiley, default_deal = 'Other', default_notes = 'Wiley prepayment discount')

    with open(outputfile, 'a') as csvfile: #APPEND TO THE SAME OUTPUTFILE
        writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
        #~ writer.writeheader()
        for doi in wiley_out_dict:
            if 'Date of acceptance' in wiley_out_dict[doi].keys():
                acceptance_date = dateutil.parser.parse(wiley_out_dict[doi]['Date of acceptance'], dateutil_wiley)
                wiley_out_dict[doi]['Date of acceptance'] = acceptance_date.strftime('%Y-%m-%d')
            writer.writerow(wiley_out_dict[doi])

    print('STATUS: Finished processing Wiley Dashboard entries')

    ###OUP
    ###MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS
    rep2oup = [
    ('Date of acceptance', ['Accepted For Publication', 'Approved For Publication']),
    #('PubMed ID', #NA
    ('DOI', ['Doi']),
    #('Publisher', #NOT A VARIABLE; DEFAULT TO OUP
    ('Journal', ['Journal Name']),
    #('E-ISSN', ['eISSN']), #NA
    #('Type of publication', #NOT A VARIABLE; DEFAULT TO ARTICLE
    ('Article title', ['Manuscript Title']),
    ('Date of publication', ['Issue Online']),
    ('Date of APC payment', ['Referral Date']),
    #('APC paid (actual currency) excluding VAT', ['Journal APC']), #NA COULD BE CALCULATED
    ('Currency of APC', ['Currency']),
    ('APC paid (£) including VAT if charged', ['Charge Amount']),
    #('Additional publication costs (£)', #NA
    #('Discounts, memberships & pre-payment agreements', #NOT A VARIABLE; DEFAULT TO OTHER
    #('Amount of APC charged to COAF grant (including VAT if charged) in £', #NA
    #('Amount of APC charged to RCUK OA fund (including VAT if charged) in £', #NA
    ('Licence', ['OUP Licence', 'Licence']),
    #('Notes', ['Comments']) #DEFAULT TO OUP PREPAYMENT DEAL
    ]
    rep2oup = collections.OrderedDict(rep2oup)

    oup_dict = {}
    rejection_dict_oup = {}
    dateutil_oup = dateutil.parser.parserinfo(dayfirst=True)
    filter_date_field_oup = 'Referral Date'
    request_status_field_oup = 'Status'
    exclude_titles_oup = ['A RELIGION OF LIFE?', 'MendelianRandomization: an R package for performing Mendelian randomization analyses using summarized data', 'Being Well, Looking Ill: Childbirth and the Return to Health in Seventeenth-Century England']
    import_prepayment_data_and_link_to_zd(oupexport, oup_dict, rejection_dict_oup, 'Doi', 'Manuscript Title', filter_date_field_oup, 'OUP', field_renaming_list = [('Status', 'OUP Status'), ('Licence', 'OUP Licence')], dateutil_options=dateutil_oup, exclude_titles=exclude_titles_oup, request_status_field=request_status_field_oup) #field_renaming_list is a list of tuples in the form (<original field in inputfile>, <new name for field in inputfile to avoid conflict with fieldnames in zd_dict>)

    excluded_debug_file = 'ART_debug_OUP_Prepayment_rejected_records.csv'
    oup_reject_fieldnames = [rejection_reason_field]
    for a in oupfieldnames:
        oup_reject_fieldnames.append(a)
    debug_export_excluded_records_prepayment(excluded_debug_file, rejection_dict_oup, oup_reject_fieldnames)

    oup_out_dict = match_datasource_fields_to_report_fields(oup_dict, rep2oup, 'Oxford University Press', 'Article', 'Other', 'Oxford University Press prepayment discount')

    with open(outputfile, 'a') as csvfile: #APPEND TO THE SAME OUTPUTFILE
        writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
        #~ writer.writeheader()
        for doi in oup_out_dict:
            if 'Date of acceptance' in oup_out_dict[doi].keys():
                acceptance_date = dateutil.parser.parse(oup_out_dict[doi]['Date of acceptance'], dateutil_oup)
                oup_out_dict[doi]['Date of acceptance'] = acceptance_date.strftime('%Y-%m-%d')
            if 'Date of publication' in oup_out_dict[doi].keys():
                publication_date = dateutil.parser.parse(oup_out_dict[doi]['Date of publication'])
                oup_out_dict[doi]['Date of publication'] = publication_date.strftime('%Y-%m-%d')
            if 'Date of APC payment' in oup_out_dict[doi].keys():
                payment_date = dateutil.parser.parse(oup_out_dict[doi]['Date of APC payment'])
                oup_out_dict[doi]['Date of APC payment'] = payment_date.strftime('%Y-%m-%d')
            writer.writerow(oup_out_dict[doi])

    print('STATUS: Finished processing OUP Prepayment entries')

    ## NOW LET'S EXPORT A CSV OF DOIS TO UPLOAD TO https://compliance.cottagelabs.com
    ## FIX THIS ONE MANUALLY ON THE OUTPUT CSV: http:/​/​dx.​doi.​org/​10.​1104/​pp.​16.​00539
    #~ with open(doifile, 'w') as csvfile:
        #~ writer = csv.DictWriter(csvfile, fieldnames=['DOI'], extrasaction='ignore')
        #~ writer.writeheader()
        #~ for ticket in report_dict:
            #~ if 'DOI' in report_dict[ticket].keys():
                #~ if report_dict[ticket]['DOI'].strip():
                    #~ writer.writerow(report_dict[ticket])

