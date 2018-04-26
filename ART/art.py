#!/usr/bin/env python3

### DEV NOTES:
## Need a new function detect_decision_ticket to parse lists of zd numbers from doi2zd_dict, title2zd_dict, etc.
## The new function should look at each of the zendesk tickets in the list and identify the one that is most likely
## to contain a decision about payment/funding:
## - Is there a DOI?
## - 'Is there an APC payment' not blank
## - ticket group is open access
## - RCUK and/or COAF payment ticked

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

### OUTPUT FILES USING THE PREFIXES BELOW LIST RECORDS FROM PREPAYMENT DEALS (SPRINGER COMPACT, WILEY, OUP)
### EACH PREPAYMENT DEAL HAS A LIST OF TITLES TO BE EXCLUDED; THE SPRINGER ONE IS exclude_titles_springer
exclude_from_next_run_prefix = "ART_info_add_to_exclusion_list_because_not_in_funders_policy_"
exclude_from_next_run_not_found_prefix = "ART_info_add_to_exclusion_list_because_not_found_in_Zendesk_"

logfile = os.path.join(working_folder, "ART_log.txt")

### THE LIST BELOW IS USED BY FUNCTION action_manually_filter_and_export_to_report_csv()
### TO EXCLUDE RECORDS FROM THE GENERATED REPORT
exclusion_list = [
    #('Article title', 'NAR Membership 2016'), #THIS ONE WAS EXCLUDED FROM RCUK REPORT 2017, BUT WILL APPEAR IN COAF REPORT 2017
    ('Description', 'zd 13598'),
    ('APC paid (£) including VAT if charged', '0.0')#THESE CONSIST OF PAYMENTS THAT WERE REFUNDED (EITHER PAID BY ANOTHER FUNDER OR REFERRED TO A PREPAYMENT DEAL
    ]

### POPULATE THE DICTIONARY BELOW (manual_title2zd_dict) WITH MATCHES
### OUTPUT TO ART_log.txt IN THE FORM:
###
### Matched zd_no:
### publisher title:
### ZD        title:
###
### THIS WILL SAVE CONSIDERABLE TIME IN SUBSEQUENT RUNS BECAUSE SIMILARITY
### SEARCHES FOR THESE TITLES WILL NOT BE NECESSARY

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
    #INPUT FOR RCUK 2017 REPORT
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
    #INPUT FOR COAF 2017 REPORT
    'Standing on the Edge – What Type of “Exclusive Licensees” Should Be Able to Initiate Patent Infringement Actions?' : '105331',
    'The Complexity of Translationally-Invariant Spin Chains with Low Local Dimension' : '127855',
    'Intimate partner homicide in England and Wales 2011-2013: pathways to prediction from multi-agency Domestic Homicide Reviews' : '105317',
    'Ultrastructural and immunocytochemical evidence for the reorganisation of the Milk Fat Globule Membrane after secretion.' : '22166',
    'ICP versus Laser Doppler Cerebrovascular Reactivity Indices to Assess Brain Autoregulatory Capacity' : '118919',
    "Forces, Friction and Fractionation: Denis Walsh's Organism, Agency and Evolution." : '102832',
    'Predicting domestic homicide and serious violence in Leicestershire with intelligence records of suicidal ideation or self-harm warnings: a retrospective analysis' : '104225',
    'How do Hunter-Gatherer Children Learn Subsistence Skills? A Meta-Ethnographic Review' : '68187',
    'Redressing Risk Oversight Failure in UK and US Listed Companies: Lessons from the RBS and Citigroup Litigation' : '81307',
    'The geodesic X-ray transform with a GL(n,C)-connection' : '120748',
    'Predicting Domestic Homicides And Serious Violence in Dorset: A Replication of Thornton’s Thames Valley Analysis' : '103157',
    'Targeting Escalation of Intimate Partner Violence: Evidence from 52,000 Offenders' : '104857',
    "There's Nothing Quasi about Quasi-Realism: Moral Realism as a Moral Doctrine" : '68568',
    'SKA aperture Array verification system: electromagnetic modeling and beam pattern measurements using a micro UAV' : '116758',
    'Hohfeldian infinities: why not to worry' : '14144',
    'Neurodegeneration and the ordered assembly of α-synuclein' : '123748',
    'In Situ Chemically-Selective Monitoring of Multiphase Displacement Processes in a Carbonate Rock Using 3D Magnetic Resonance Imaging' : '134308',
    'Modelling of spray flames with Doubly Conditional Moment Closure' : '132855',
    'What works in conservation? Using expert assessment of summarised evidence to identify practices that enhance natural pest control in agriculture' : '17129',
    'The thickness of the crystal mush on the floor of the Bushveld magma chamber' : '133741',
    'Clinical Implications of Germline Mutations in Breast Cancer Genes -RECQL' : '123730',
    'Powerful Qualities and Pure Powers' : '84364',
    'Diagnostic evaluation of Magnetization Transfer and Diffusion Kurtosis imaging for prostate cancer detection in a re-biopsy population' : '127858',
    'Linear Waves in the Interior of Extremal Black Holes II' : '127852',
    "Functional morphology in paleobiology: origins of the method of 'paradigms'" : '84914',
    'In defence of substantial sentencing discretion' : '106411',
    'Integrated case management of repeated intimate partner violence: a randomized, controlled trial' : '103521',
    'Numerical study of a sphere descending along an inclined slope in a liquid' : '126414',
    'Data processing for the sandwiched Rényi divergence: a condition for equality' : '41706',
    'Combining different models' : '107533',
    'The Invisibility of Diffeomorphisms' : '118788',
    'Unstable mode solutions to the Klein-Gordon equation in Kerr-anti-de Sitter spacetimes' : '38709',
    'Gender patterns in academic entrepreneurship' : '19129',
    'Application of a multi-gene next-generation sequencing panel to a non-invasive oesophageal cell-sampling device to diagnose dysplastic Barrett?s oesophagus' : '103034',
    'TIBLE: a web-based, freely accessible resource for small-molecule binding data for mycobacterial species' : '89577',
    ###WILEY
    # 'Refining Genotype-Phenotype Correlation in Alström Syndrome Through Study of Primary Human Fibroblasts' : '81394',
    # 'The canine POMC gene, obesity in Labrador retrievers and susceptibility to diabetes mellitus' : '39491',
    ##WILEY SIMILARITY MATCHES
    # 'From ?Virgin Births? to ?Octomom?: Representations of single motherhood via sperm donation in the UK media' : '30491',
    # 'Prognostic models for identifying adults with intellectual disabilities and mealtime support needs who are at greatest risk of respiratory infection and emergency hospitalization' : '74902',
    # 'Using predictions from a joint model for longitudinal and survival data to inform the optimal time of intervention in an abdominal aortic aneurysm screening programme' : '72229',
    # 'Markov models for ocular fixation locations in the pres- ence and absence of colour' : '69352',
    ###OUP
    'Changes over time in the health and functioning of older people moving into care homes: Analysis of data from the English Longitudinal Study of Ageing' : '76550',
    'Disease-free and overall survival at 3.5 years for neoadjuvant bevacizumab added to docetaxel followed by fluorouracil, epirubicin and cyclophosphamide, for women with HER2 negative early breast cancer: ARTemis Trial.' : '81145',
    'Cancer immunotherapy trial registrations increase exponentially but chronic immunosuppressive glucocorticoid therapy may compromise outcomes' : '81604',
    """Swinburneâ€™s <i>Atalanta In Calydon</i>: 
    Prosody as sublimation in Victorian â€˜Greekâ€™ tragedy""" : '18350',
    "Reading the Exeter Book Riddles as Life-Writing" : '63449',
    #INPUT FOR COAF 2017 REPORT
    'Cancer Hallmarks Analytics Tool (CHAT): A text mining approach to organise and evaluate scientific literature on cancer' : '100405',
    'A.J. Nickerson on Hardy' : '92942', #Hardy’s Apprehensions
    '?What Utopia Would Feel Like?: Lars Von Trier?s ?Dancer in the Dark' : '39170',
    }


# SOMETIMES PREPAYMENT DEALS REPORTS HAVE ROWS WITH DOIs, BUT NO ARTICLE TITLE
# THIS IS USUALLY NOT AN ISSUE BECAUSE THIS SCRIPT USES DOIs AS THE PRIMARY
# MATCHING FIELD FOR ZD LOOKUP. HOWEVER, IF A DOI IS UNKNOWN TO ZD AND APOLLO
# THE ONLY WAY OF MATCHING AN ARTICLE TO ZD WILL BE TO MANUALLY ENTER THESE
# PROBLEMATIC RECORDS IN THE DICTIONARY BELOW, SO THAT A MATCH BASED ON TITLE
# CAN BE ATTEMPTED
manual_doi2title = {
    # SPRINGER COMPACT
    '10.1007/s11244-017-0806-0' : 'Modification of Ammonia Decomposition Activity of Ruthenium Nanoparticles by N-Doping of CNT Supports',
    '10.1007/s41887-017-0016-9' : 'Tracking Police Responses to “Hot” Vehicle Alerts: Automatic Number Plate Recognition and the Cambridge Crime Harm Index',
    '10.1007/s11081-016-9323-4' : 'Riemannian optimization and multidisciplinary design optimization',
    '10.1007/s11125-016-9383-4' : 'Education of children with disabilities in India and Pakistan: Critical analysis of developments in the last 15 years',
    '10.1007/s11244-016-0653-4' : 'H2 Production via Ammonia Decomposition Using Non-Noble Metal Catalysts: A Review'
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
rejected_coaf_payment_dict = {}
included_coaf_payment_dict = {}



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
                if type(zd_number) == type('string'):
                    for field in row.keys():
                        if (field in zd_dict[zd_number].keys()) and (row_counter == 0):
                            print('WARNING: Dictionary for ZD ticket', zd_number, 'already contains a field named', field + '. It will be overwritten by the value in file', metadata_file)
                    zd_dict[zd_number].update(row)
                elif type(zd_number) == type(['list']): ### zd_number can now be a tuple because doi2zd_dict now includes all matching tickets for a given DOI as a tuple
                    for zd in zd_number:
                        zd_dict[zd].update(row)
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

def plog(*args, logfilename=logfile, terminal=True):
    '''
    A function to print arguments to a log file
    :param args: the argumes to output
    :param terminal: if set to false, suppresses terminal output
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
    :param title: the title we are trying to match (e.g. title of article in prepayment deal csv)
    :param publisher: the name of the publisher
    :param title2zd_dict: a dictionary of zendesk tickets, indexed by title
    :param policy_dict: a dictionary of zendesk tickets covered by a funder's policy, indexed by title
    :return:
    '''
    plog('INFO: Attempting heuristic_match_by_title for', title)
    unresolved_titles_sim = []
    possible_matches = []
    out_of_policy = []
    if policy_dict:
        plog('DEBUG: policy_dict:', policy_dict)
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
            plog('### Matched zd_no: ' + zd_number)
            plog('publisher title: ' + title + '\n')
            plog('ZD        title: ' + most_similar_title.lower() + '\n')
            plog("Entry for manual_title2zd_dict: '" + title + "' : '" + zd_number + "',\n\n\n")
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
                plog('### Matched zd_no (OUT OF FUNDER POLICY): ',  zd_number)
                plog('publisher title: ' + title + '\n')
                plog('ZD        title: ' + most_similar_title.lower() + '\n')
                plog("Entry for manual_title2zd_dict: '" + title + "' : '", zd_number, "',\n\n\n")
            else:
                unresolved_titles_sim.append(title)
                print('\nWARNING:', publisher, 'record could not be matched to ZD:\n', title, '\n')
            zd_number = ''
        exclude_from_next_run = os.path.join(working_folder, exclude_from_next_run_prefix + publisher.upper() + '.txt')
        with open(exclude_from_next_run, 'a') as f:
            for i in out_of_policy:
                f.write("'''" + i[0].strip() + "''', ")
    else:
        plog('DEBUG: policy_dict is empty')
        for t in title2zd_dict.keys():
            # print('t:', t)
            similarity = similar(title.upper(), t)
            if similarity > 0.8:
                possible_matches.append((similarity, t))
        if len(possible_matches) > 0:
            possible_matches.sort(reverse=True)
            most_similar_title = possible_matches[0][1]
            zd_number = title2zd_dict[most_similar_title]
            plog('Matched zd_no (match attempted using title2zd_dict): ', zd_number)
            plog('publisher title: ' + title + '\n')
            plog('ZD        title: ' + most_similar_title.lower() + '\n')
            plog('''Please review the match above; if it is a correct match, please include this record in manual_title2zd_dict.
                Notice that matching by title currently identifies the ticket containg the most similar title in Zendesk, which might not
                necessarily be the ticket containing the decision (info on funders' policies, etc.''')
        else:
            unresolved_titles_sim.append(title)
            print('\nWARNING:', publisher, 'record could not be matched to ZD:\n', title, '\n')
        zd_number = ''
    exclude_from_next_run = os.path.join(working_folder, exclude_from_next_run_not_found_prefix + publisher.upper() + '.txt')
    with open(exclude_from_next_run, 'a') as f:
        for i in unresolved_titles_sim:
            f.write("'''" + i.strip() + "''', ")
    plog('DEBUG: zd_number returned by heuristic_match_by_title:', zd_number)
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
    exclude_from_next_run = os.path.join(working_folder, exclude_from_next_run_prefix + publisher.upper() + '.txt')
    with open(exclude_from_next_run, 'a') as f:
        for i in out_of_policy:
            f.write(i[0] + ', ')
    return(zd_number)

def match_prepayment_deal_to_zd(doi, title, publisher, doi2zd_dict, doi2apollo, apollo2zd_dict, title2zd_dict, institution='University of Cambridge', restrict_to_funder_policy=False):
    '''
    This function attempts to match the DOI of a publication to zendesk data;
    if that fails, it calls a separate function to perform a match
    based on title similarity (heuristic_match_by_title).
    :param doi: a string containing the DOI of the publication
    :param title: a string containing the title of the publication
    :param publisher: a string containing the publisher of the publication
    :param doi2zd_dict: a dictionary translating DOIs to zendesk numbers
    :param doi2apollo: a dictionary translating DOIs to apollo handles
    :param apollo2zd_dict: a dictionary translating apollo handles to zendesk numbers
    :param institution: string containing the institution of the publication
    :param restrict_to_funder_policy: if set to 'RCUK' or 'COAF' matches by title are performed using only zendesk
        tickets flagged as included in those funders policies or payments
    :return: zendesk_number or an empty string # tuple (zendesk_number, reason_zendesk_number_could_not_be_found)
    '''

    # DEV NOTES
    # Maybe I should change this function so that zd_numbers are appended to a list of possible matches
    # using each of the different search methods (doi, apollo handle, title).
    # The problem with the current approach is that if we find a false match based on doi,
    # the other search methods are not tried. It saves time, but need to decide if
    # false matches are too many or too serious a problem to compensate the time saved.

    # Maybe a good solution would be to perform all searches, but use dictionary that has been
    # restricted to tickets in the OA group rather than the entire ZD dataset.

    unresolved_dois = []
    unresolved_dois_apollo = []
    unresolved_titles = []
    unresolved_titles_sim = []
    if institution == 'University of Cambridge':
        if title.strip() in manual_title2zd_dict.keys():
            zd_number = manual_title2zd_dict[title.strip()]
            if not zd_number:
                return('')
        else:
            try:
                zd_number = doi2zd_dict[doi]
                # if '10.1093/brain/awx101' in doi: ##DEBUGGING STUFF
                #     print('DOI:', doi)
                #     print('zd_number:', zd_number)
                #     print('title:', title)
            except KeyError:
                unresolved_dois.append(doi)
                try:
                    apollo_handle = doi2apollo[doi]
                    zd_number = apollo2zd_dict[apollo_handle]
                except KeyError:
                    unresolved_dois_apollo.append(doi)
                    if title.strip() == '':
                        try:
                            title = manual_doi2title[doi]
                        except KeyError:
                            plog('WARNING: Empty title for prepayment record with DOI', doi, 'not found in manual_doi2title dictionary.', terminal=true)
                    try:
                        if restrict_to_funder_policy == 'RCUK':
                            zd_number = title2zd_dict_RCUK[title.upper()]
                        elif restrict_to_funder_policy == 'COAF':
                            zd_number = title2zd_dict_COAF[title.upper()]
                        else:
                            zd_number = title2zd_dict[title.upper()]
                    except KeyError:
                        unresolved_titles.append(title)
                        possible_matches = []
                        if restrict_to_funder_policy == 'RCUK':
                            zd_number = heuristic_match_by_title(title, publisher, title2zd_dict, policy_dict=title2zd_dict_RCUK)
                        elif restrict_to_funder_policy == 'COAF':
                            zd_number = heuristic_match_by_title(title, publisher, title2zd_dict, policy_dict=title2zd_dict_COAF)
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
    # plog('unresolved_dois:', unresolved_dois)
    # plog('unresolved_dois_apollo:', unresolved_dois_apollo)
    # plog('unresolved_titles:', unresolved_titles)
    return(zd_number)

def import_prepayment_data_and_link_to_zd(inputfile, output_dict, rejection_dict, doi_field,
                                          title_field, filter_date_field, publisher, institution_field = '',
                                          field_renaming_list = [], dateutil_options='', exclude_titles = [],
                                          request_status_field='', delim=','): #field_renaming_list is a list of tuples in the form (<original field in inputfile>, <new name for field in inputfile to avoid conflict with fieldnames in zd_dict>)
    '''
    This function reads an input CSV file containing one publication per row. For each row,
    it attempts to match the publication to zendesk data based on doi (preferred) or
    similarity of publication title.

    This function also filters prepayment data so that only papers matching zd tickets with
    funder policy or payment flags set to 'yes' are included in output_dict (and ultimately in
    the report).

    :param inputfile: input CSV file containing publication data
    :param output_dict: an output dictionary containing all the matched data
    :param rejection_dict: an output dictionary containing all records in inputfile, with
                            rejection info for those not included in output_dict and zd data
                            for all records matched to zd (included or excluded)
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
            manual_rejection = 'BUG: unknown reason for manual rejection'
            t = filter_prepayment_records(row, publisher, filter_date_field, request_status_field, dateutil_options)
            if t[0] == 1: ## first parameter returned by filter_prepayment_records is either 1 for include or 0 for exclude
                doi = row[doi_field]
                # print('Publisher:', publisher)
                # print('DOI:', doi)
                title = row[title_field]
                if institution_field:
                    institution = row[institution_field]
                else:
                    institution = 'University of Cambridge'
                if not title.strip() in exclude_titles:
                    a = match_prepayment_deal_to_zd(doi, title, publisher, doi2zd_dict, doi2apollo,
                                                    apollo2zd_dict, title2zd_dict, institution,
#                                                    restrict_to_funder_policy=reporttype # default is None, so comment this line for a comprehensive search
                                                    ) ##global reporttype is either 'COAF' or 'RCUK'
                    zd_number = a
                    manual_rejection = 'Not found in zd (function match_prepayment_deal_to_zd returned an empty string)'
                else:
                    zd_number = ''
                    manual_rejection = 'Title included in exclude_titles list; Not found in zd (match by title attempted only on tickets included in ' + reporttype + ' policy) during a previous run'
                    plog('''WARNING: The following record could not be matched to a Zendesk ticket. 
                        If this is a Wiley or OUP record, please map it manually to a Zendesk by adding it to
                        manual_title2zd_dict.''')
                #~ output_dict[publisher_id] = row
                for a in field_renaming_list:
                    #~ output_dict[publisher_id][a[1]] = output_dict[publisher_id][a[0]]
                    row[a[1]] = row[a[0]]
                    #~ del output_dict[publisher_id][a[0]]
                    del row[a[0]]
                if (type(zd_number) == type('string')) and zd_number.strip():
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
                    if reporttype == 'RCUK':
                        policy_flag = "RCUK policy [flag]"
                        payment_flag = "RCUK payment [flag]"
                    elif reporttype == 'COAF':
                        policy_flag = "COAF policy [flag]"
                        payment_flag = "COAF payment [flag]"
                    if type(zd_number) == type('string'):
                        row.update(zd_dict[zd_number])
                        if zd_number in included_in_report.keys():
                            print('WARNING: A report entry already exists for zd number:', zd_number)
                            print('TITLE:', title)
                            print('Please merge this duplicate in the exported report', '\n')
                        if (zd_dict[zd_number][policy_flag] == 'yes') or (zd_dict[zd_number][payment_flag] == 'yes'):
                            #row.update(zd_dict[zd_number])
                            row[rejection_reason_field] = 'Included in output_dict by function import_prepayment_data_and_link_to_zd (zd_number is string)'
                            output_dict[publisher_id] = row
                            rejection_dict[publisher_id] = row # this can be removed from the if statement as it also appears in else; leaving it here for now as still in active development
                        else:
                            row[rejection_reason_field] = 'Not included in ' + reporttype + ' policy (zd_number is string)'
                            rejection_dict[publisher_id] = row
                    elif type(zd_number) == type(['list']): ## zd_number may be a tuple because doi2zd_dict now resolves all tickets with a given DOI that are not explicitly marked as duplicates in zd
                        included_row_flag = False
                        for zd in zd_number:
                            if included_row_flag == False:
                                row.update(zd_dict[zd])
                                if zd in included_in_report.keys():
                                    print('WARNING: A report entry already exists for zd number:', zd)
                                    print('TITLE:', title)
                                    print('Please merge this duplicate in the exported report', '\n')
                                if (zd_dict[zd][policy_flag] == 'yes') or (zd_dict[zd][payment_flag] == 'yes'):
                                    row[rejection_reason_field] = 'Included in output_dict by function import_prepayment_data_and_link_to_zd (zd_number is list)'
                                    output_dict[publisher_id] = row
                                    rejection_dict[publisher_id] = row  # this can be removed from the if statement as it also appears in else; leaving it here for now as still in active development
                                    included_row_flag = True
                            else:
                                print('INFO: This row has already been included in output_dict based on another zendesk ticket:')
                                print('INFO: Current zendesk ticket:', zd)
                                print('INFO: List of zendesk tickets being evaluated for this input row:', zd_number)
                                print('INFO: This input row:', row, '\n')
                        if included_row_flag == False:
                            row[rejection_reason_field] = 'Not included in ' + reporttype + ' policy (zd_number is list)'
                            rejection_dict[publisher_id] = row
                else:
                    row[rejection_reason_field] = t[1] + '; ' + manual_rejection
                    # print(t[0])
                    # print(row)
                    # print(row[rejection_reason_field])
                    rejection_dict[publisher_id] = row
            else:
                row[rejection_reason_field] = t[1]
                rejection_dict[publisher_id] = row
            publisher_id += 1


def filter_prepayment_records(row, publisher, filter_date_field, request_status_field='', dateutil_options=''):
    '''
    This function filters out prepayment records that:
    - were not approved for payment
    - are not an article (some prepayment deals report top ups together with article data)
    - are not within the reporting period

    It returns a tuple, where the first element is an integer (0 for excluded records; 1 for included)
    and the second element is a string specifying the reason for exclusion (if excluded)

    It is not possible to implemented filtering based on values of zendesk fields here
    because this function operates on raw data coming from the prepayment deal; it is
    not linked to zd data yet.

    :param row:
    :param publisher:
    :param filter_date_field:
    :param request_status_field:
    :param dateutil_options:
    :return:
    '''
    prune = 0 # Include records in report by default
    prune_reason = 'BUG: this record was excluded without evaluation by function filter_prepayment_records'
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
            # plog(publisher, publication_date, 'included in reporting period by function filter_prepayment_records')
            # plog(row)
            # plog('\n\n')
            prune_reason = ''
            return(1, prune_reason)
        else:
            # plog(publisher, publication_date, 'EXCLUDED FROM reporting period by function filter_prepayment_records')
            # plog(row)
            # plog('\n\n')
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
    with open(os.path.join(working_folder, unmatched_payment_file_prefix + rcuk_paymentsfilename), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rcuk_paymentsfieldnames)
        writer.writeheader()
    with open(os.path.join(working_folder, unmatched_payment_file_prefix + coaf_paymentsfilename), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=coaffieldnames)
        writer.writeheader()
    with open(os.path.join(working_folder, nonJUDB_payment_file_prefix + rcuk_paymentsfilename), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rcuk_paymentsfieldnames)
        writer.writeheader()
    with open(os.path.join(working_folder, nonEBDU_payment_file_prefix + rcuk_paymentsfilename), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rcuk_paymentsfieldnames)
        writer.writeheader()


debug_problematic_doi_list = [ ### list of DOIs that appear in more than one zendesk ticket ; not used anywhere; safe to delete
    '10.1021/acs.macromol.5b02667',
    '10.2337/dc15-2078',
    '10.1101/gad.293027.116',
    '10.1063/1.4964601',
    '10.1007/s00125-016-3905-8',
    '10.1093/nar/gkw560',
    '10.17863/CAM.6700',
    '10.1515/rle-2016-0046',
    '10.1016/j.rser.2016.09.107',
    '10.1038/cddis.2016.302',
    '10.1038/ncomms10069',
    '10.1016/j.molbiopara.2016.07.004',
    '10.1016/j.jclepro.2016.06.155',
    '10.1210/jc.2015-3854',
    '10.1080/09537287.2016.1147099',
    '10.1038/nphys4168',
    '10.1063/1.4958727',
    '10.1371/journal.pone.0150686',
    '10.1007/s12028-017-0404-9',
    '10.1136/bmjopen-2015-009974',
    '10.1017/jfm.2016.408',
    '10.1016/j.lcsi.2016.09.005',
    '10.1016/j.vaccine.2016.08.002',
    '10.1061/9780784479827.229',
    '10.1016/j.conbuildmat.2016.09.086',
    '10.1111/ajt.14433',
    '10.1111/ane.12594',
    '10.1017/S0007114516001859',
    '10.1534/genetics.115.183285',
    '10.1680/jcoma.16.00034',
    '10.1002/acn3.366',
    '10.1186/s12913-016-1379-5',
    '10.1113/JP270717',
    '10.1530/ERC-16-0251',
    '10.1089/neu.2016.4442',
    '10.1017/jfm.2016.16',
    '10.1088/0953-8984/28/1/01LT01',
    '10.14814/phy2.12836',
    '10.1177/1744806916636387',
    '10.1088/0264-9381/33/13/135002',
    '10.3847/2041-8205/829/1/L11',
    '10.1021/acsami.6b04041',
    '10.1186/s12889-017-4170-6',
    '10.1016/j.pbi.2016.10.007',
    '10.1093/nar/gkw783',
    '10.1074/mcp.R115.052902',
    '10.1111/cen.13011',
    '10.1016/j.sna.2015.11.003',
    '10.1039/c7ra02590d',
    '10.1007/s00442-016-3608-3',
    '10.1038/tp.2016.271',
    '10.1680/jensu.15.00015',
    '10.1016/j.ces.2016.04.004',
    '10.1136/thoraxjnl-2016-208402',
    '10.7554/eLife.22848',
    '10.1186/s12889-016-3184-9',
    '10.1080/01441647.2016.1200156',
    '10.1016/j.euroneuro.2016.07.010',
    '10.17863/CAM.6653',
    '10.1103/PhysRevB.93.144201',
    '10.1371/journal.pmed.1002139',
    '10.1038/ng.3699',
    '10.1016/j.jclepro.2016.12.048',
    '10.7717/peerj.2746',
    '10.1107/S2059798315013236',
    '10.1016/j.shpsb.2015.08.004',
    '10.1016/j.jmb.2016.04.025',
    '10.1088/0022-3727/49/11/11LT01',
    '10.1136/bjsports-2016-096083',
    '10.1186/s12889-016-3192-9',
    '10.1371/journal.pone.0160512',
    '10.1148/radiol.2017160150',
    '10.1177/0954406215616984',
    '10.1140/epjc/s10052-017-5199-5',
    '10.1017/S0963548314000194',
    '10.1063/1.4941760',
    '10.1109/ISIT.2016.7541418',
    '10.1088/0953-8984/28/34/345504',
    '10.1007/s12583-015-0643-7',
    '10.1186/s13041-016-0279-2',
    '10.1093/indlaw/dwv034',
    '10.1007/s11229-016-1294-7',
    '10.1039/c0ib00149j',
    '10.1016/j.neuroimage.2016.07.022',
    '10.1021/acsami.5b07026',
    '10.3389/fpsyg.2016.01902',
    '10.1371/journal.ppat.1005948',
    '10.1136/jnnp-2017-316402',
    '10.18632/oncotarget.8308',
    '10.1002/eji.201545537',
    '10.17863/CAM.6118',
    '10.1371/journal.ppat.1006055',
    '10.1177/1468087416656946',
    '10.1002/2016GB005570',
    '10.7554/eLife.09617',
    '10.1111/oik.02622',
    '10.1136/bmjspcare-2015-001059',
    '10.1186/s13326-016-0085-x',
    '10.1016/j.tem.2017.06.004',
    '10.1111/jsbm.12230',
    '10.1038/ncomms10781',
    '10.1016/j.jmb.2015.12.018',
    '10.1186/s40814-016-0071-1',
    '10.1021/acs.est.6b04746',
    '10.3389/fimmu.2017.00298',
    '10.1016/j.cell.2016.09.037',
    '10.1192/bjp.bp.116.190165',
    '10.1089/neu.2015.4134',
    '10.1093/brain/awx101',
    '10.1001/jamapsychiatry.2015.3058',
    '10.1099/mic.0.000184',
    '10.1109/HRI.2016.7451745',
    '10.1098/rsfs.2016.0018',
    '10.1177/0269216315627125',
    '10.1038/lsa.2016.255',
    '10.1038/srep35333',
    '10.1007/s00199-016-0992-1',
    'http://www.cs.rochester.edu/u/tetreaul/bea12proceedings.pdf',
    '10.1017/jfm.2017.200',
    '10.1037/a0038524',
    '10.1063/1.4937473',
    '10.1016/j.dib.2016.11.028',
    '10.1007/s10437-016-9211-5',
    '10.3390/cancers8090077',
    '10.1021/jacs.6b09334',
    '10.1093/mnras/stw2958',
    '10.1038/nature21039',
    '10.1177/1932296815604439',
    'https://www.repository.cam.ac.uk/handle/1810/255727',
    '10.1038/srep44283',
    '10.1136/jnnp-2016-313918',
    '10.1016/j.neuroimage.2016.08.012',
    '10.1111/1471-0528.14385',
    '10.1016/j.stemcr.2017.05.033',
    '10.1042/BCJ20160041',
    '10.1109/TPEL.2016.2587757',
    '10.1111/criq.12260',
    '10.1103/PhysRevB.95.054412',
    '10.1016/j.neuint.2016.11.012',
    '10.1038/ng.3751',
    '10.1002/gepi.22001',
    'No DOI'
    ]

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
    '''
    This function iterates through zd_dict after it has received data from all possible sources.
    It then selects tickets that will be included in the report, based on the following criteria:
    -

    I THINK THIS FUNCTION IS NOT DOING WHAT IT SHOULD BE DOING FOR COAF PAYMENTS; FIX IT

    :return:
    '''
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
                ### QUICK AND DIRTY FIX FOR COAF REPORT; ALMOST CERTAINLY BREAKS RCUK REPORT GENERATION
                report_dict[a] = zd_dict[a]
                ### END OF QUICK AND DIRTY FIX FOR COAF REPORT
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
    reconcile_file = os.path.join(working_folder, reconcile_prefix + rcuk_paymentsfile.split('/')[-1])
    reconcile_file_coaf = os.path.join(working_folder, reconcile_prefix + coaf_paymentsfile.split('/')[-1])
    reconcile_field = 'report_status'
    reconcile_fieldnames = rcuk_paymentsfieldnames + [reconcile_field]
    reconcile_fieldnames_coaf = coaffieldnames + [reconcile_field]
    with open(reconcile_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=reconcile_fieldnames, extrasaction='ignore')
        writer.writeheader()
        for p in rejected_rcuk_payment_dict:
            rejected_rcuk_payment_dict[p][reconcile_field] = 'excluded'
            writer.writerow(rejected_rcuk_payment_dict[p])
        for p in included_rcuk_payment_dict:
            included_rcuk_payment_dict[p][reconcile_field] = 'included'
            writer.writerow(included_rcuk_payment_dict[p])
    with open(reconcile_file_coaf, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=reconcile_fieldnames_coaf, extrasaction='ignore')
        writer.writeheader()
        for p in rejected_coaf_payment_dict:
            rejected_coaf_payment_dict[p][reconcile_field] = 'excluded'
            writer.writerow(rejected_coaf_payment_dict[p])
        for p in included_coaf_payment_dict:
            included_coaf_payment_dict[p][reconcile_field] = 'included'
            writer.writerow(included_coaf_payment_dict[p])

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
invoice2zd_number = {
    ##INPUT FOR RCUK 2017 REPORT
    'APC502145176':'48547',
    'P09819649':'28975',
    'Polymers-123512':'15589',
    'Polymers-123512/BANKCHRG':'15589',
    '9474185' : '18153',
    ##INPUT FOR COAF 2017 REPORT
    '19841M2' : '87254',
    '20170117' : '50542',
    '94189700 BANKCHRG' : '47567'
}

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
rcuk_paymentsfilename = "RCUK_merged_payments_file.csv"
rcuk_paymentsfile = os.path.join(working_folder, rcuk_paymentsfilename)
merge_csv_files([rcuk_veje, rcuk_veji, rcuk_vejj], rcuk_paymentsfile)
# coaf_last_year = os.path.join(working_folder, 'veag45.csv')
# coaf_this_year = os.path.join(working_folder, 'veag50.csv')
coaf_paymentsfilename = "VEAG50_Dec2017_edited.csv"#"VEAG050_2017-10-31_edited.csv"
coaf_paymentsfile = os.path.join(working_folder, coaf_paymentsfilename)
# merge_csv_files([coaf_last_year, coaf_this_year], coaf_paymentsfile)
zenexport = os.path.join(working_folder, "export-2017-11-09-2150-5703871969.csv")
zendatefields = os.path.join(working_folder, "rcuk-report-active-date-fields-for-export-view-2017-11-13-2307.csv")
apolloexport = os.path.join(working_folder, "Apollo_all_items-20171110.csv")
cottagelabsDoisResult = os.path.join(working_folder, "DOIs_for_cottagelabs_2017-11-21_results_edited.csv")
cottagelabsTitlesResult =  os.path.join(working_folder, "Titles_for_cottagelabs_2017-11-21_results_edited.csv")
cottagelabsexport = os.path.join(working_folder, "Cottagelabs_results.csv")
merge_csv_files([cottagelabsDoisResult, cottagelabsTitlesResult], cottagelabsexport)
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
report_end_date = datetime.datetime(2017, 9, 30, hour = 23, minute = 59, second = 59)
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

### DEVELOPMENT NOTES:
## All translation dictionaries 2zd_dict should be adapted to take lists as values because of duplicates in Zendesk;
## once this is done, the functions using these dictionaries can be edited to expect lists, rather than sometimes strings
## and sometimes lists.

doi2zd_dict = {} #Dictionary mapping DOI to zd number; each of this dictionary's values may be a string if there is only one zd number matching the given DOI, or a list if more than one match were found during populating
apollo2zd_dict = {} #Dictionary mapping apollo handle to zd number
oa2zd_dict = {} #Dictionary mapping OA number to zd number
zd2zd_dict = {} #Dictionary mapping zd number to zd number, so that we can use general function plug_in_metadata to match a zd export to another zd export
title2zd_dict = {} #Dictionary mapping article title to zd number; each of this dictionary's values may be a string if there is only one zd number matching the given DOI, or a list if more than one match were found during populating
zd_dict = {}
zd_dict_RCUK = {} #A dictionary of tickets that have either RCUK policy or RCUK payment ticked. Needed for title matching because of the SE duplicates, which have an article title, but no decision
zd_dict_COAF = {} #A dictionary of tickets that have either COAF policy or COAF payment ticked. Needed for title matching because of the SE duplicates, which have an article title, but no decision
title2zd_dict_RCUK = {}
title2zd_dict_COAF = {}
doi2apollo = {} #Dictionary mapping doi to handle (created using data from apollo export)
zd2oa_dups_dict = {} #Dictionary mapping zendesk tickets marked as duplicates to the OA number of their master ticket

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
    springerfieldnames = extract_csv_header(springercompactexport, enc="utf-8", delim=';')
    wileyfieldnames = extract_csv_header(wileyrcukcoaf, "utf-8")
    oupfieldnames = extract_csv_header(oupexport, "utf-8")
    rejection_reason_field = 'Reason for exclusion'

    allfieldnames = zendeskfieldnames + zendatefieldnames + rcuk_paymentsfieldnames + apollofieldnames + coaffieldnames
    # allfieldnames += cottagelabsfieldnames + springerfieldnames + wileyfieldnames + oupfieldnames


    #~ #pprint(allfieldnames)
    #~ #raise

    ##CLEANUP DEBUG INFO FROM PREVIOUS RUNS BY WRITING HEADERS
    print('STATUS: cleanning up debug info from previous run')
    action_cleanup_debug_info()

    ###INDEX INFO FROM ZENDESK ON ZD NUMBER
    plog('STATUS: indexing zendesk info on zd number', terminal=True)
    action_index_zendesk_data()

    ### POPULATE doi2apollo DICTIONARY
    plog('STATUS: populating doi2apollo dictionary', terminal=True)
    action_populate_doi2apollo(apolloexport)

    #### PLUGGING IN DATA FROM ZENDESK DATE FIELDS
    plog('STATUS: plugging in data from zendesk date fields into zd_dict', terminal=True)
    plug_in_metadata(zendatefields, 'id', zd2zd_dict)

    # #### ESTIMATE COMPLIANCE VIA GREEN ROUTE
    # plog('STATUS: estimating compliance via the green route', terminal=True)
    # ### TAKE A SAMPLE OF OUTPUTS COVERED BY THE RCUK POLICY AND PUBLISHED DURING THE REPORTING PERIOD
    # ### EXCLUDE ZD TICKETS MARKED AS DUPLICATES OR "WRONG VERSION"
    # rcuk_dict = {}
    # for a in zd_dict:
    #     row = zd_dict[a]
    #     rcuk_policy = row['RCUK policy [flag]']
    #     ticket_creation = dateutil.parser.parse(row['Created at'])
    #     wrong_version = row['Wrong version [flag]']
    #     dup = row['Duplicate [flag]']
    #     #~ if not row['Online Publication Date (YYYY-MM-DD) [txt]'] == '-':
    #         #~ try:
    #             #~ publication_date = dateutil.parser.parse(row['Online Publication Date (YYYY-MM-DD) [txt]'].replace('--','-'))
    #         #~ except ValueError:
    #             #~ print(row['Online Publication Date (YYYY-MM-DD) [txt]'])
    #             #~ raise
    #     #~ else:
    #         #~ try:
    #             #~ if not row['Publication Date (YYYY-MM-DD) [txt]'] == '-':
    #                 #~ publication_date = dateutil.parser.parse(row['Publication Date (YYYY-MM-DD) [txt]'])
    #             #~ else:
    #                 #~ publication_date = datetime.datetime(2100, 1, 1)
    #         #~ except KeyError:
    #             #~ publication_date = datetime.datetime(2100, 1, 1)
    #     if (rcuk_policy == 'yes') and (wrong_version != 'yes') and (dup != 'yes') and (green_start_date <= ticket_creation <= green_end_date):
    #         rcuk_dict[a] = zd_dict[a]
    #
    # ## CHECK HOW MANY OF THOSE ARE GOLD, GREEN OR UNKNOWN
    # green_dict = {}
    # gold_dict = {}
    # green_counter = 0
    # gold_counter = 0
    # apc_payment_values = ['Yes', 'Wiley Dashboard', 'OUP Prepayment Account', 'Springer Compact']
    # WoS_total = 2400 #From Web of Science: number of University of Cambridge publications (articles, reviews and proceeding papers) acknowledging RCUK funding during the green reporting period
    # for a in rcuk_dict:
    #     row = rcuk_dict[a]
    #     apc_payment = row['Is there an APC payment? [list]']
    #     green_version = row['Green allowed version [list]']
    #     embargo = row['Embargo duration [list]']
    #     green_licence = row['Green licence [list]']
    #     if apc_payment in apc_payment_values:
    #         gold_counter += 1
    #         gold_dict[a] = rcuk_dict[a]
    #     else:
    #         green_counter += 1
    #         green_dict[a] = rcuk_dict[a]
    #
    # rcuk_papers_total = gold_counter + green_counter
    #
    # plog('RESULT --- COMPLIANCE VIA GREEN/GOLD ROUTES:', terminal = True)
    # plog(str(rcuk_papers_total), 'ZD tickets covered by the RCUK open access policy were created during the green reporting period, of which:', terminal=True)
    # plog(str(gold_counter), '(' + str(gold_counter / rcuk_papers_total) + ') tickets were placed in the GOLD route to comply with the policy', terminal=True)
    # plog(str(green_counter), '(' + str(green_counter / rcuk_papers_total) + ') tickets were placed in the GREEN route to comply with the policy', terminal=True)
    # plog('RESULT --- COMPLIANCE VIA GREEN/GOLD ROUTES AS A RATIO OF WoS TOTAL:', terminal = True)
    # plog(str(WoS_total), 'papers (articles, reviews and proceedings papers) acknowledging RCUK funding were published by the University of Cambridge during the green reporting period, of which:', terminal=True)
    # plog(str(gold_counter / WoS_total), 'complied via the GOLD route', terminal = True)
    # plog(str(green_counter / WoS_total), 'complied via the GREEN route', terminal = True)
    #
    # #~ raise

    #### PLUGGING IN DATA FROM THE RCUK AND COAF PAYMENTS SPREADSHEETS
    plug_in_payment_data(rcuk_paymentsfile, rcuk_paymentsfieldnames, 'Description', total_rcuk_payamount_field,
                         'Page, colour or membership amount', amount_field = rcuk_payamount_field,
                         file_encoding = 'utf-8', transaction_code_field = 'Tran', funder = 'RCUK')
    plug_in_payment_data(coaf_paymentsfile, coaffieldnames, 'Comment', total_coaf_payamount_field,
                         'COAF Page, colour or membership amount', invoice_field = 'Invoice',
                         amount_field = coaf_payamount_field, file_encoding = 'utf-8', funder = 'COAF')

    #### PLUGGING IN DATA FROM APOLLO
    ###NEED TO MAP THIS DATA USING REPOSITORY HANDLE, BECAUSE APOLLO DOES
    ###NOT STORE ZD AND OA NUMBERS FOR ALL SUBMISSIONS
    plug_in_metadata(apolloexport, 'handle', apollo2zd_dict)

    #### PLUGGING IN DATA FROM COTTAGELABS
    ## For some reason not all PMIDs are appearing in the final COAF 2017 report, so this is something that needs to be fixed.
    try:
        plug_in_metadata(cottagelabsexport, 'DOI', doi2zd_dict)
    except FileNotFoundError:
        plog('WARNING: Compliance data from Cottage Labs not found; I will assume this is because it was not generated yet',
             terminal=True)

    #### MAUALLY FIX SOME PROBLEMS
    zd_dict['3743']['DOI'] = '10.1088/0953-2048/27/8/082001'
    zd_dict['3743']['externalID [txt]'] = 'OA-1128'
    zd_dict['3743']['Date of acceptance'] = '2014-06-11'
    zd_dict['3743']['Publisher'] = 'IOP'
    zd_dict['3743']['Journal'] = 'Superconductor Science and Technology'
    zd_dict['3743']['Type of publication'] = 'Article'
    zd_dict['3743']['Article title'] = 'A Trapped Field of 17.6 T in Melt-Processed, Bulk Gd-Ba-Cu-O Reinforced with Shrink-Fit Steel'
    zd_dict['3743']['Date of publication'] = '2014-06-25'
    zd_dict['3743']['Fund that APC is paid from (1)'] = 'RCUK'
    zd_dict['3743']['Funder of research (1)'] = 'EPSRC'
    zd_dict['3743']['Grant ID (1)'] = 'EP/K02910X/1'
    zd_dict['3743']['Licence'] = 'CC BY'

    #### NOW THAT WE PLUGGED IN ALL DATA SOURCES INTO THE ZENDESK EXPORT,
    #### PRODUCE THE FIRST PART OF THE REPORT (PAYMENTS LINKED TO ZENDESK)
    report_dict = {}
    ### START BY FILTERING WHAT WE NEED
    action_populate_report_dict()

    #### EXPORT PAYMENTS IN ORIGINAL FORMAT WITH AN EXTRA COLUMN "INCLUDED/EXCLUDED FROM REPORT"
    #### FOR RECONCILIATION/DEBUGGING:
    action_export_payments_reconciliation()

    #### NOW ADJUST TOTAL APC VALUES FOR TICKETS WHERE THE APC WAS SPLIT BETWEEN
    #### RCUK AND COAF
    action_adjust_total_apc_values()

    ### POPULATE REPORT FIELDS WITH DATA FROM ZD/APOLLO/PAYMENT FIELDS
    ### CONVERT DATA WHEN NEEDED
    action_populate_report_fields()

    excluded_recs = {}
    included_in_report = {}

    report_fields = extract_csv_header(report_template, "utf-8")
    custom_rep_fields = ['id',                      # ZD number from zd
                         'externalID [txt]',        # OA number from zd
                         'Reason for exclusion',    # field calculated and appended by ART
                         # 'Description',             # field from CUFS (RCUK)
                         # 'Ref 1',                   # field from CUFS (RCUK)
                         # 'Ref 5',                   # field from CUFS (RCUK)
                         'Comment',                 # field from CUFS (COAF)
                         'Invoice',                 # field from CUFS (COAF)
                         'RCUK policy [flag]',      # from zd
                         'RCUK payment [flag]',     # from zd
                         'COAF policy [flag]',      # from zd
                         'COAF payment [flag]',     # from zd
                         'handle'                   # from Apollo
                         ]
    report_fieldnames = report_fields + custom_rep_fields #+ rcuk_paymentsfieldnames
#    report_fieldnames = report_fields ###UNCOMMENT THIS LINE FOR FINAL VERSION

    ### THEN EXPORT THE INCLUDED TICKETS TO THE REPORT CSV
    action_manually_filter_and_export_to_report_csv()

    ### EXPORT EXCLUDED RECORDS TO CSVs
    excluded_debug_file = os.path.join(working_folder, 'ART_debug_payments_matched_to_zd_tickets_excluded_from_report.csv')
    debug_export_excluded_records(excluded_debug_file, excluded_recs_logfile, excluded_recs)

    #### ADD DATA FROM PUBLISHER DEALS TO THE END OF THE REPORT
    institution_filter = ['University of Cambridge']
    prepayment_debug_fields = ["Id",                    # zd number
                               "COAF policy [flag]",    # list of fields to include in debug files for all
                               "COAF payment [flag]",   # prepayment details
                               "RCUK policy [flag]",
                               "RCUK payment [flag]",
                               "Is there an APC payment? [list]"
                               ]


    ### SPRINGER
    ### MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS
    rep2springer = [
    ('Date of acceptance', ['acceptance date']),
    #('PubMed ID', #NA
    ('DOI', ['DOI']),
    #('Publisher', #NOT A VARIABLE; DEFAULT TO SPRINGER
    ('Journal', ['journal title']),
    ('E-ISSN', ['eISSN']),
    #('Type of publication', #NOT A VARIABLE; DEFAULT TO ARTICLE
    ('Article title', ['article title']),
    ('Date of publication', ['online first publication date', 'online issue publication date']),
    #('Date of APC payment', #NA
    ('APC paid (actual currency) excluding VAT', ['APC']),
    ('Currency of APC', ['currency']),
    #('APC paid (£) including VAT if charged', #NA
    #('Additional publication costs (£)', #NA
    #('Discounts, memberships & pre-payment agreements', #NOT A VARIABLE; DEFAULT TO SPRINGER COMPACT?
    #('Amount of APC charged to COAF grant (including VAT if charged) in £', #NA
    #('Amount of APC charged to RCUK OA fund (including VAT if charged) in £', #NA
    ('Licence', ['license type']),
    ('Notes', ['FundNames'])
    ]
    rep2springer = collections.OrderedDict(rep2springer)

    springer_dict = {}
    rejection_dict_springer = {}
    dateutil_springer = dateutil.parser.parserinfo() ## this used to be dateutil.parser.parserinfo(dayfirst=True) for old Springer Compact reports
    exclude_titles_springer = [
        ### RCUK REPORT 2017
        # 'Clinical Trials in Vasculitis',
        # 'PET Imaging of Atherosclerotic Disease: Advancing Plaque Assessment from Anatomy to Pathophysiology',
        # 'Consequences of tidal interaction between disks and orbiting protoplanets for the evolution of multi-planet systems with architecture resembling that of Kepler 444',
        # 'Hunter-Gatherers and the Origins of Religion',
        # 'A 2-adic automorphy lifting theorem for unitary groups over CM fields',
        # 'Basal insulin delivery reduction for exercise in type 1 diabetes: finding the sweet spot',
        # 'Hohfeldian Infinities: Why Not to Worry',
        # 'Ultrastructural and immunocytochemical evidence for the reorganisation of the milk fat globule membrane after secretion',
        # 'Data processing for the sandwiched Rényi divergence: a condition for equality',
        # 'Knowledge, beliefs and pedagogy: how the nature of science should inform the aims of science education (and not just when teaching evolution)',
        # 'Gender patterns in academic entrepreneurship'
        ### COAF REPORT 2017
        ## NOT FOUND IN ZENDESK
        '''Do Gang Injunctions Reduce Violent Crime? Four Tests in Merseyside, UK''',
        '''"Don't Mind the Gap!" Reflections on improvement science as a paradigm''',
        '''Paradoxical effects of self-awareness of being observed: Testing the effect of police body-worn cameras on assaults and aggression against officers''',
        '''KYC Optimization Using Distributed Ledger Technology''', '''Metric ultraproducts of classical groups''',
        '''Uniformity of the late points of random walk on''',
        '''Nowhere differentiable functions of analytic type on products of finitely connected planar domains''',
        '''Advocacy Science: Explaining the term with case studies from biotechnology''',
        '''Turn-taking in cooperative offspring care: by-product of individual provisioning behavior or active response rule?''',
        '''Fetal Androgens and Human Sexual Orientation: Searching for the Elusive Link''',
        '''The Coevolution of Play and the Cortico-Cerebellar System in Primates''',
        '''Police Attempts to Predict Domestic Murder and Serious Assaults: Is Early Warning Possible Yet?''',
        '''Does tracking and feedback boost patrol time in hot spots? Two tests.''',
        '''Finite vs. Small Strain Discrete Dislocation Analysis of Cantilever Bending of Single Crystals''',
        '''Effect of context on the contribution of individual harmonics to residue pitch''',
        '''Preferred location for conducting filament formation in thin-film nano-ionic electrolyte: Study of microstructure by atom-probe tomography''',
        '''Volumetric Growth Rates of Meningioma and its Correlation with Histological Diagnosis and Clinical Outcome: A Systematic Review''',
        '''Crack kinking at the tip of a mode I crack in an orthotropic solid''',
        '''Evidence comes by replication, but needs differentiation: The reproducibility problem in science and its relevance for criminology''',
        '''Comparing representations for function spaces in computable analysis''',
        '''Spatial selectivity in cochlear implants: Effects of asymmetric waveforms and development of a single-point measure.''',
        '''Tracking Police Responses to “Hot” Vehicle Alerts: Automatic Number Plate Recognition and the Cambridge Crime Harm Index''',
        '''A re-examination of the effect of masker phase curvature on non-simultaneous masking''',
        '''Tracking Police Responses to “Hot” Vehicle Alerts: Automatic Number Plate Recognition and the Cambridge Crime Harm Index''',
        ]
    import_prepayment_data_and_link_to_zd(springercompactexport, springer_dict, rejection_dict_springer,
                                          'DOI', 'article title', # this used to be 'Article Title' in Springer Compact reports,
                                          'approval requested date', # 'Online Publication Date' was previously used, but it was renamed to 'online first publication date' and has blank values for several articles
                                          'Springer',
                                          institution_field='membership institute', # this used to be 'Institution',
                                          dateutil_options=dateutil_springer,
                                          exclude_titles=exclude_titles_springer,
                                          delim=';')

    excluded_debug_file = os.path.join(working_folder, 'ART_debug_Springer_Compact_rejected_records.csv')
    springer_reject_fieldnames = [rejection_reason_field]
    for a in prepayment_debug_fields:
        springer_reject_fieldnames.append(a)
    for a in springerfieldnames:
        springer_reject_fieldnames.append(a)
    #pprint(rejection_dict_springer)
    debug_export_excluded_records_prepayment(excluded_debug_file, rejection_dict_springer, springer_reject_fieldnames)

    springer_out_dict = match_datasource_fields_to_report_fields(springer_dict, rep2springer,
                                                                 'Springer', 'Article', 'Springer Compact',
                                                                 'Springer Compact')

    report_fieldnames += ['Is there an APC payment? [list]']
    with open(outputfile, 'a') as csvfile: #APPEND TO THE SAME OUTPUTFILE
        writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
        #~ writer.writeheader()
        for doi in springer_out_dict:
            if 'Date of publication' in springer_out_dict[doi].keys():
                publication_date = springer_out_dict[doi]['Date of publication']
                publication_date = dateutil.parser.parse(publication_date, dateutil_springer)
                springer_out_dict[doi]['Date of publication'] = publication_date.strftime('%Y-%m-%d')
            if 'Date of acceptance' in springer_out_dict[doi].keys():
                acceptance_date = dateutil.parser.parse(springer_out_dict[doi]['Date of acceptance'], dateutil_springer)
                springer_out_dict[doi]['Date of acceptance'] = acceptance_date.strftime('%Y-%m-%d')
            writer.writerow(springer_out_dict[doi])

    plog('STATUS: Finished processing Springer Compact entries')

    ### WILEY
    ###MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS
    rep2wiley = [
    ('Date of acceptance', ['Article Accepted Date']),
    #('PubMed ID', #NA
    ('DOI', ['Wiley DOI']),             ## Fields in Wiley report are 'DOI' and 'Publisher', but I had to append 'Wiley ' to these two lines
    ('Publisher', ['Wiley Publisher']), ## because ART has a mechanism that prevents existing fields (e.g. comming from zd) from being overwritten
    ('Journal', ['Journal']),           ## by data from prepayment deals; this is something that probably needs revising because it is confusing, not obvious
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
    exclude_titles_wiley = [
        ## RCUK REPORT 2017
        # 'Chromatin determinants impart camptothecin sensitivity'
        ## COAF REPORT 2017
        # '''Incremental Material Flow Analysis with Bayesian Inference''',
        # '''Assessing the Impact of Germination and Sporulation Conditions on the Adhesion of Bacillus Spores to Glass and Stainless Steel by Fluid Dynamic Gauging''',
        # '''A new Mississippian tetrapod from Fife, Scotland, and its environmental context.''',
        # '''Causal narratives in public health: the difference between mechanisms of aetiology and mechanisms of prevention in non-communicable diseases''',
        # '''High imensional change point estimation via sparse projection''',
        # '''Random projection ensemble classification''',
        ]
    import_prepayment_data_and_link_to_zd(wileyexport, wiley_dict, rejection_dict_wiley, 'DOI', 'Article Title',
                                          filter_date_field_wiley, 'Wiley',
                                          field_renaming_list = [('Journal Type', 'Wiley Journal Type'),
                                                                 ('DOI', 'Wiley DOI'), ('Publisher', 'Wiley Publisher')],
                                          dateutil_options=dateutil_wiley, exclude_titles=exclude_titles_wiley,
                                          request_status_field=request_status_field_wiley) #field_renaming_list is a list of tuples in the form (<original field in inputfile>, <new name for field in inputfile to avoid conflict with fieldnames in zd_dict>)

    excluded_debug_file = os.path.join(working_folder, 'ART_debug_Wiley_Dashboard_rejected_records.csv')
    wiley_reject_fieldnames = [rejection_reason_field]
    for a in prepayment_debug_fields:
        wiley_reject_fieldnames.append(a)
    for a in wileyfieldnames:
        wiley_reject_fieldnames.append(a)
    debug_export_excluded_records_prepayment(excluded_debug_file, rejection_dict_wiley, wiley_reject_fieldnames)

    wiley_out_dict = match_datasource_fields_to_report_fields(wiley_dict, rep2wiley, default_deal = 'Other', default_notes = 'Wiley prepayment discount')

    # for a in wiley_dict:
    #     print(wiley_dict[a].keys())
    #     print('DOI', wiley_dict[a]['Wiley DOI'])
    #     print('Publisher:', wiley_dict[a]['Wiley Publisher'])

    with open(outputfile, 'a') as csvfile: #APPEND TO THE SAME OUTPUTFILE
        writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
        #~ writer.writeheader()
        for doi in wiley_out_dict:
            if 'Date of acceptance' in wiley_out_dict[doi].keys():
                acceptance_date = dateutil.parser.parse(wiley_out_dict[doi]['Date of acceptance'], dateutil_wiley)
                wiley_out_dict[doi]['Date of acceptance'] = acceptance_date.strftime('%Y-%m-%d')
            writer.writerow(wiley_out_dict[doi])

    plog('STATUS: Finished processing Wiley Dashboard entries')

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
    dateutil_oup = dateutil.parser.parserinfo() # Used for RCUK report but no longer valid: dateutil.parser.parserinfo(dayfirst=True)
    filter_date_field_oup = 'Referral Date'
    request_status_field_oup = 'Status'
    exclude_titles_oup = [
        ## RCUK REPORT 2017
        # 'A RELIGION OF LIFE?', 'MendelianRandomization: an R package for performing Mendelian randomization analyses using summarized data',
        # 'Being Well, Looking Ill: Childbirth and the Return to Health in Seventeenth-Century England'
        ## COAF REPORT 2017
        # '''Rethinking folk culture in twentieth-century Britain''',
        # '''The thickness of the mushy layer on the floor of the Skaergaard magma chamber at apatite saturation''',
        # '''?What Utopia Would Feel Like?: Lars Von Trier?s ?Dancer in the Dark''',
        # '''Blocking Strategies and Stability of Particle Gibbs Samplers''',
        # '''A.J. Nickerson on Hardy''',
        ]
    import_prepayment_data_and_link_to_zd(oupexport, oup_dict, rejection_dict_oup, 'Doi', 'Manuscript Title',
                                          filter_date_field_oup, 'OUP',
                                          field_renaming_list = [('Status', 'OUP Status'), ('Licence', 'OUP Licence')],
                                          dateutil_options=dateutil_oup, exclude_titles=exclude_titles_oup,
                                          request_status_field=request_status_field_oup) #field_renaming_list is a list of tuples in the form (<original field in inputfile>, <new name for field in inputfile to avoid conflict with fieldnames in zd_dict>)

    excluded_debug_file = os.path.join(working_folder, 'ART_debug_OUP_Prepayment_rejected_records.csv')
    oup_reject_fieldnames = [rejection_reason_field]
    for a in prepayment_debug_fields:
        oup_reject_fieldnames.append(a)
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

    plog('STATUS: Finished processing OUP Prepayment entries')

    # NOW LET'S EXPORT A CSV OF DOIS TO UPLOAD TO https://compliance.cottagelabs.com
    # FIX THIS ONE MANUALLY ON THE OUTPUT CSV: http:/​/​dx.​doi.​org/​10.​1104/​pp.​16.​00539
    with open(doifile, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['DOI'], extrasaction='ignore')
        writer.writeheader()
        for ticket in report_dict:
            if 'DOI' in report_dict[ticket].keys():
                if report_dict[ticket]['DOI'].strip():
                    writer.writerow(report_dict[ticket])

