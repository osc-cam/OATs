#!/usr/bin/env python3

### DEV NOTES:
## Need a new function detect_decision_ticket to parse lists of zd numbers from doi2zd_dict, title2zd_dict, etc.
## The new function should look at each of the zendesk tickets in the list and identify the one that is most likely
## to contain a decision about payment/funding:
## - Is there a DOI?
## - 'Is there an APC payment' not blank
## - ticket group is open access
## - RCUK and/or COAF payment ticked

## Bug: using exclusion_list, this script supresses the output of any articles where 'APC paid (£) including VAT if charged'
## is zero. This works well in most cases, but it will also exclude papers where funds were used to pay for
## "Additional publication costs (£)" only.

import collections
import csv
import datetime
import logging
import logging.config
import os
import re
try:
    import dateutil.parser
except ModuleNotFoundError:
    print('WARNING: Could not load the dateutil module. Please install it if you have admin rights. Conversion of dates will not work properly during this run')

from pprint import pprint
from difflib import SequenceMatcher

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


### SET UP WORKING FOLDER
home = os.path.expanduser("~")
#working_folder = os.path.join(home, 'OATs', 'ART-wd')
#working_folder = os.path.join(home, 'Dropbox', 'OSC', 'ART-wd')
#working_folder = os.path.join(home, 'Dropbox', 'Midas-wd')
working_folder = os.path.join(home, 'OATs', 'Midas-wd')

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

### USE THE LIST BELOW TO FORCE THE INCLUSION OF TICKETS MARKED AS DUPLICATES IN ZENDESK IN zd_dict
manual_zendesk_duplicates_to_include = ['36495', '76842', '86232', '83197', '89212']

### USE THIS DICTIONARY TO FORCE THE MAPPING OF PARTICULARLY PROBLEMATIC OA NUMBERS TO ZD NUMBERS
### FOR EXAMPLE A OA NUMBER MARKED AS DUPLICATE IN ZENDESK, BUT WITH A PAYMENT ASSOCIATED WITH IT
### (SO NOT EASY TO FIX IN ZENDESK)
manual_oa2zd_dict = {
    'OA-13907':'83033',
    'OA-10518':'36495',
    'OA-13111':'76842',
    'OA-14062':'86232',
    'OA-13919':'83197',
    'OA-14269':'89212'
    }

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
    #INPUT FOR COAF 2018 REPORT
    'A Critical Review on the Contributions of Chemical and Physical Factors towards the Nucleation and Growth of Large-area Graphene': '152886',
    'Detecting vortices within unsteady flows when using single-shot PIV.': '193498',
    'Outcomes of Cartilage Repair Techniques for Chondral Injury in the Hip - A Systematic Review': '169792',
    'Detecting changes in sediment overburden using distributed temperature sensing - an experimental and numerical study': '219786',
    "The Role of Gender Role Attitudes and Immigrant Generation in Ethnic Minority Women's Labor Force Participation in Britain": '182551',
    'Developmental Aspects of Schizotypy and Suspiciousness: A Review': '157901',
    'Effects of microclimatic and human parameters on outdoor thermal sensation in the high-density tropical context of Dhaka': '222109',
    'Laser-induced incandescence particle image velocimetry (LII-PIV) for two phase flow velocity measurement': '228318',
    'Ab initio approach and its impact on superconductivity': '230030',
    'Virtual Reality Hip Arthroscopy Simulator Demonstrates Sufficient Face Validity': '209718',
    'Diet, Sex and Social Status in the Late Avar Period: Stable Isotope Investigations at Nuštar Cemetery, Croatia': '178012',
    'Optimal Cerebral Perfusion Pressure via Transcranial Doppler in TBI: Application of Robotic Technology': '227673',
    'Superficial and Multiple Calcifications and Ulceration Associate with Intraplaque Hemorrhage in the Carotid Atherosclerotic Plaque': '190381',
    "A Note on Horwich's Notion of Grounding": '180649',
    'WHO/ISUP classification, grading and pathological staging of renal cell carcinoma: standards and controversies': '220201',
    'The first plant bast fibre technology: identifying splicing in archaeological textiles': '209951',
    'ENT audit and research in the era of trainee collaboratives': '199140',
    'Maltreated children use more grammatical negations.': '125128',
    "Against Crane's Psychologistic Account of Intentionality": '163352',
    'The Provenance, Use, and Circulation of Metals in the European Bronze Age: The State of Debate': '203755',
    'Notch sensitivity of orthotropic solids : interaction of tensile and shear damage zones': '225967',
    'Midline Shift is Unrelated to Subjective Pupillary Reactivity Assessment on Admission in Moderate and Severe Traumatic Brain Injury': '171132',
    'On the Development and Early Observations from a Towing Tank Based Transverse Wing-Gust Encounter Test Rig': '216392',
    'Turbulent drag reduction using anisotropic permeable substrates': '183366',
    'What experiments on pinned nanobubbles can tell about the critical nucleus for bubble nucleation': '147190',
    'Temperature and strain rate effects on the mechanical properties of a polymer bonded explosive': '230813',
    'cGMP at the centre of attention: Emerging strategies for activating the cardioprotective PKG pathway': '180647',
    'Sliding to Predict: Vision-Based Beating Heart Motion Estimation by Modeling Temporal Interactions': '152890',
    '3D imaging of cells in scaffolds: direct labelling for micro CT': '193471',
    'Effect of screening for type 2 diabetes on healthcare costs: a register-based study among 139,075 individuals diagnosed with diabetes in Denmark between 2001 and 2009': '170726',
    "Pressing for Sentence? An Examination of the New Zealand Crown Prosecutor's Role in Sentencing": '200128',
    'The homeostatic ensemble for cells': '240521',
    'The swimming of a deforming helix': '229319',
    'Critical Thresholds for Intracranial Pressure Vary Over Time in Non-Craniectomized Traumatic Brain Injury Patients': '183590',
    'Editorial Comment: Structured Reporting of Pelvic MRI Leads to Better Treatment Planning of Uterine Leiomyomas': '176008',
    '''"Sovereign" Islam and Tatar "Aqīdah": Normative Religious Narratives and Grassroots Criticism amongst Tatarstan's Muslims''': '229341',
    'Pharmacological management of post-traumatic seizures in adults: current practice patterns in the United Kingdom and the Republic of Ireland': '223365',
    'Local alkylating chemotherapy applied immediately after 5-ALA guided resection of Glioblastoma does not provide additional benefit': '173013',
    'Buber, educational technology and the expansion of dialogic space': '166314',
    'Association of Subchondral Bone Texture on Magnetic Resonance Imaging with Radiographic Knee Osteoarthritis Progression: Data from the Osteoarthritis Initiative Bone Ancillary Study': '178030',
    'From "Gut Feeling" to Objectivity: Machine Preservation of the Liver as a Tool to Assess Organ Viability': '152455',
    'Genetics of antigen processing and presentation': '223355',
    'Cognitive Flexibility and Religious Disbelief': '199818',
    'Alperin-McKay natural correspondences in solvable and symmetric groups for the prime p=2': '132355',
    'Prioritising Risk Factors for Type 2 Diabetes: Causal Inference Through Genetic Approaches': '188212',
    'Kuhnian revolutions in neuroscience: the role of tool development': '188188',
    'A comparison of semi-automated volumetric versus linear measurement of small vestibular schwannomas': '152037',
    'Active quenching technique: quench acceleration and protection': '163744',
    'Diet and food strategies in a southern al-Andalusian urban environment during Caliphal period, Écija, Sevilla.': '223614',
    'MoS2/C/C Nanofiber with Double Layer Carbon Coating for High Cycling Stability and Rate Capability Lithium-Ion Battery': '246799',
    'Hereditary renal cell carcinoma syndromes: diagnosis, surveillance and management': '181971',
    'The British Neurosurgical Trainee Research Collaborative: Five Years On': '123453',
    'Quality of life outcomes in patients with localised renal cancer: a literature review': '214502',
    'Cortical bone mapping: measurement and statistical analysis of localised skeletal changes': '218558',
    'A Multi-Dimensional Spatial Lag Panel Data Model with Spatial Moving Average Nested Random Effects Errors': '153065',
    'Timelike completeness as an obstruction to C^0-extensions': '133238',
    ###WILEY
    # 'Refining Genotype-Phenotype Correlation in Alström Syndrome Through Study of Primary Human Fibroblasts' : '81394',
    # 'The canine POMC gene, obesity in Labrador retrievers and susceptibility to diabetes mellitus' : '39491',
    ##WILEY SIMILARITY MATCHES
    # 'From ?Virgin Births? to ?Octomom?: Representations of single motherhood via sperm donation in the UK media' : '30491',
    # 'Prognostic models for identifying adults with intellectual disabilities and mealtime support needs who are at greatest risk of respiratory infection and emergency hospitalization' : '74902',
    # 'Using predictions from a joint model for longitudinal and survival data to inform the optimal time of intervention in an abdominal aortic aneurysm screening programme' : '72229',
    # 'Markov models for ocular fixation locations in the pres- ence and absence of colour' : '69352',
    #INPUT FOR RCUK 2018 REPORT
    'Anomalous Diffusion-Assisted Brightness in White Cellulose Nanofibril Membranes' : '157022', # matched by ART to wrong ZD ticket (usually dataset supporting...)
    'A New Versatile Route to Unstable Diazo Compounds via Oxadiazolines and Use In Aryl-Alkyl Cross-Coupling Reactions' : '133470', # matched by ART to wrong ZD ticket (usually dataset supporting...)
    'On Chip Andreev Devices: hard Superconducting Gap and Quantum Transport in Ballistic Nb-In0.75Ga0.25As quantum well-Nb Josephson junctions' : '96458', # matched by ART to wrong ZD ticket (usually dataset supporting...)
    'Extracting Crystal Chemistry from Amorphous Carbon Structures' : '69685', # matched by ART to wrong ZD ticket (usually dataset supporting...)
    'The anti-feminist reconstruction of the midlife crisis: Popular psychology, journalism, and social science in 1970s America' : '153923', # match not found by ART
    'Kv4.2 channel activity controls intrinsic firing dynamics of arcuate kisspeptin neurons' : '143299', # match not found by ART
    'Understanding LiOH Chemistry in a Ruthenium Catalyzed Li-O2 Battery' : '130559', # match not found by ART
    'Enhanced permeability and binding activity of isobutylene-grafted peptides' : '133734', # match not found by ART
    'A Lewis Base Catalysis Approach for the Photoredox Activation of Boronic Acidsand Esters' : '127851', # match not found by ART
    'Inkjet printed nanocavities on a photonic crystal template' : '116287', # match not found by ART
    'Meta Selective C-H Borylation of Benzylamine, Phenethylamine and Phenylpropylamine-Derived Amides Enabled by a Single Anionic Ligand' : '114744', # match not found by ART
    'A Faustian bargain for universities?' : '109023', # match not found by ART (Wiley error: Article title: LncRNA GAS5 inhibits microglial M2 polarization and exacerbates demyelination)
    'Strongly Enhanced Photovoltaic Performance and Defect Physics of Air-Stable Bismuth Oxyiodide (BiO' : '91052', # match not found by ART
    'High imensional change point estimation via sparse projection' : '98711', # match not found by ART
    'MMP-13 binds to platelet receptors αIIbβ3 and GPVI and impairs aggregation and thrombus formation' : '164103', # match not found by ART
    'Random projection ensemble classification' : '78583', # match not found by ART
    'Specificity effects of amino acid substitutions in promiscuous hydrolases-context-dependence of catalytic residue contributions to local fitness landscapes in nearby sequence space' : '71156', # match not found by ART
    'Lymphotoxin and lipopolysaccharide induce NF‐κB‐p52 generation by a co‐translational mechanism' : '127412', # match not found by ART (Wiley error: Article title: Transposon-driven transcription is a conserved feature of vertebrate spermatogenesis and transcript evolution)
    #INPUT FOR RCUK 2019 REPORT
    'Chronic fetal hypoxia disrupts the peri-conceptual environment in next-generation adult female rats': '297396',
    '''Context and Implications Document for: Secondary students’ proof constructions in mathematics: the role of written vs. oral mode of argument representation''': '232497',
    'Synthesis of structurally diverse N-substituted quaternary carbon containing small molecules from á,á-disubstituted propargyl amino esters': '213758',
    'IL-1? cleavage by inflammatory caspases of the non-canonical inflammasome controls the senescence-associated secretory phenotype': '316701',
    'Naïve Realism, Seeing Stars,and Perceiving the Past': '177450',
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
    #INPUT FOR RCUK 2018 REPORT
    'Unexpected corporate outcomes from hedge fund activism in Japan' : '156418', # match not found by ART
    'Dysglycaemia, inflammation and psychosis: findings from the U.K. ALSPAC birth cohort' : '174630', # match not found by ART
    #INPUT FOR RCUK 2019 REPORT
    "T. S. Eliot and the Point of Intersesction": "210756",
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

def output_debug_info(outcsv, row_dict, csvheader = []):
    '''
    This function appends a row to an output CSV file
    :param outcsv: path of output CSV file
    :param row_dict: dictionary containing the row to be output
    :param csvheader: the header of the CSV file
    '''
    with open(outcsv, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csvheader, extrasaction='ignore')
        writer.writerow(row_dict)

rejected_rcuk_payment_dict = {}
included_rcuk_payment_dict = {}
rejected_coaf_payment_dict = {}
included_coaf_payment_dict = {}

def plug_in_payment_data(paymentsfile, fileheader, oa_number_field, output_apc_field, output_pagecolour_field,
                         invoice_field = 'Ref 5', amount_field = 'Amount', file_encoding = 'charmap',transaction_code_field = 'Tran',
                         source_funds_code_field = 'SOF', funder = 'RCUK'):
    '''
    This function parses financial reports produced by CUFS. It tries to mach each payment in the CUFS report
    to a zd ticket and, if successful, it produces summations of payments per zd ticket and appends these
    values to zd_dict as output_apc_field and/or output_pagecolour_field

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
    logger.info('oa2zd_dict.keys(): {}'.format(sorted(oa2zd_dict.keys())))
    logger.info('oa2zd_dict[OA-12501]: {}'.format(oa2zd_dict['OA-12501']))
    t_oa = re.compile("OA[ \-]?[0-9]{4,8}")
    t_zd = re.compile("ZD[ \-]?[0-9]{4,8}")
    payments_dict_apc = {}
    payments_dict_other = {}
    with open(paymentsfile, encoding=file_encoding) as csvfile:
        reader = csv.DictReader(csvfile)
        row_counter = 0
        unmatched_oa_numbers = []
        for row in reader:
            logger.debug('row: {}'.format(row))
            if row[oa_number_field] in oa_number_typos.keys():
                row[oa_number_field] = oa_number_typos[row[oa_number_field]]
            #print('\n', 'oa_number_field:', oa_number_field)
            m_oa = t_oa.search(row[oa_number_field].upper())
            m_zd = t_zd.search(row[oa_number_field].upper())
            #before = row[oa_number_field]
            if m_oa:
                oa_number = m_oa.group().upper().replace("OA" , "OA-").replace(" ","").replace('--', '-')
                try:
                    zd_number = manual_oa2zd_dict[oa_number]
                except KeyError:
                    try:
                        zd_number = oa2zd_dict[oa_number]
                    except KeyError:
                        ### MANUAL FIX FOR OLD TICKET
                        if oa_number == "OA-1128":
                            zd_number = '3743' #DOI: 10.1088/0953-2048/27/8/082001
                        elif oa_number == "OA-1515":
                            zd_number = '4323'
                        else:
                            if oa_number not in unmatched_oa_numbers:
                                unmatched_oa_numbers.append(oa_number)
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
                                    logger.warning('Dictionary for ZD ticket {} already contains a field named {}. '
                                                   'It will be overwritten by the value in file {}'.format(zd_number,
                                                                                                field, paymentsfile))
                            zd_dict[zd_number].update(payments_dict_other[zd_number]) #http://stackoverflow.com/questions/8930915/append-dictionary-to-a-dictionary
                        else:
                            ## NOT A EBDU, EBDV OR EBDW PAYMENT
                            key = 'not_EBD*_payment_' + str(row_counter)
                            if funder == 'RCUK':
                                rejected_rcuk_payment_dict[key] = row
                            debug_filename = os.path.join(working_folder, nonEBDU_payment_file_prefix + paymentsfile.split('/')[-1])
                            output_debug_info(debug_filename, row, fileheader)
                    else:
                        ## NOT A JUDB PAYMENT
                        key = 'not_JUDB_payment_' + str(row_counter)
                        if funder == 'RCUK':
                            rejected_rcuk_payment_dict[key] = row
                        debug_filename = os.path.join(working_folder, nonJUDB_payment_file_prefix + paymentsfile.split('/')[-1])
                        output_debug_info(debug_filename, row, fileheader)
                else:
                ##PAYMENTS SPREADSHEET DOES NOT CONTAIN TRANSACTION FIELD
                ##WE MUST ASSUME ALL PAYMENTS ARE APCs
                    key = 'no_transaction_field_' + str(row_counter)
                    if funder == 'RCUK':
                        included_rcuk_payment_dict[key] = row.copy()
                        logger.debug('RCUK payments without a transaction field detected in file {}'.format(
                                        paymentsfile))
                    elif funder == 'COAF':
                        included_coaf_payment_dict[key] = row.copy()
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
                elif funder == 'COAF':
                    rejected_coaf_payment_dict[key] = row
                debug_filename = os.path.join(working_folder, unmatched_payment_file_prefix + paymentsfile.split('/')[-1])
                output_debug_info(debug_filename, row, fileheader)
            row_counter += 1
        if unmatched_oa_numbers:
            unmatched_oa_numbers.sort()
            logger.warning("ZD numbers could not be found for the following OA numbers in {}: {}. Data for these OA numbers "
                       "will NOT be exported.".format(paymentsfile, unmatched_oa_numbers))


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
            if matching_field in ['doi', 'DOI']:
                mf = prune_and_cleanup_string(mf, DOI_CLEANUP)
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
    :param dict: the reporting dictionary
    :param zd_list: list of zendesk data fields that may be used to populate the output fields
    :param report_field_list: list of output report fields that should be populated with data from
                                fields in zd_list
    :param ticket: dictionary representation of ZD ticket to work on
    :return:
    '''
    used_funders = []
    for fund_f in report_field_list: #e.g. Fund that APC is paid from (1)(2) and (3)
        for zd_f in zd_list: #'RCUK payment [flag]', 'COAF payment [flag]', etc
            if (fund_f not in ticket.keys()) and (zd_f not in used_funders):
            ## 'Fund that APC is paid from 1, 2 or 3' NOT YET SET FOR THIS TICKET
                if '[flag]' in zd_f:
                    if ticket[zd_f].strip().upper() == 'YES':
                        #print('zdfund2funderstr[zd_f]:', zdfund2funderstr[zd_f])
                        ticket[fund_f] = zdfund2funderstr[zd_f]
                        used_funders.append(zd_f)
                else:
                    if not ticket[zd_f].strip() == '-':
                        #print(ticket[zd_f]:', ticket[zd_f])
                        ticket[fund_f] = ticket[zd_f]
                        used_funders.append(zd_f)
    return ticket

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

def prune_and_cleanup_string(string, pruning_list, typo_dict={}):
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
    if typo_dict.keys() and (string in typo_dict.keys()):
        string = typo_dict[string]
    return(string.strip())

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

def match_prepayment_deal_to_zd(doi, title, publisher, doi2zd_dict, doi2apollo, apollo2zd_dict, title2zd_dict,
                                institution='University of Cambridge', restrict_to_funder_policy=False):
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

    def ticket_in_policy(zd_ticket):
        '''
        Check if ZD ticket is marked as included in funder policies
        :param zd_ticket: Zendesk ticket to evaluate
        :return: True if included in at least one policy; False if not included
        '''
        for field in ["RCUK policy [flag]", "COAF policy [flag]", "RCUK payment [flag]", "COAF payment [flag]"]:
            if (zd_ticket[field] == 'yes'):
                return True
        return False

    def doi_match(doi):
        '''
        Matches DOI to a list of Zendesk tickets usig dictionaries doi2zd_dict, doi2apollo and zd_dict. If a match is
        found, checks if ticket is included in funder policies. If it is, returns the ZD number of the matched ticket;
        otherwise return None
        :param doi: DOI to lookup
        :return: zd_number or None
        '''
        try:
            zd_list = doi2zd_dict[doi]
        except KeyError:
            zd_list = []

        if not zd_list:
            try:
                apollo_handle = doi2apollo[doi]
                zd_list = apollo2zd_dict[apollo_handle]
            except KeyError:
                zd_list = []

        if zd_list:
            logger.debug('zd_list: {}'.format(zd_list))
            for zd_number in zd_list:
                zd_ticket = zd_dict[zd_number]
                if ticket_in_policy(zd_ticket):
                    return zd_number
        return None

    def title_match(title, doi):
        if title.strip() == '':
            try:
                title = manual_doi2title[doi]
            except KeyError:
                logger.warning('Empty title for prepayment record with DOI {} '
                               'not found in manual_doi2title dictionary'.format(doi))
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
        return zd_number


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
            return zd_number
        else:
            zd_number = doi_match(doi)
            if not zd_number:
                zd_number = title_match(title, doi)

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
    :param field_renaming_list: list of fields in prepayment dataset that should be renamed to avoid conflict with
                                fields in other input datasets.
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
            # calculate and add discount data to row
            if publisher == 'Wiley':
                row['Prepayment discount'] = '£{}'.format(row['Discount'])
            elif publisher == 'OUP':
                discount = '{0:.2f}'.format((float(row['Charge Amount'])/0.95) - float(row['Charge Amount']))
                row['Prepayment discount'] = '£{}'.format(discount)
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
                    logger.warning('The following record could not be matched to a Zendesk ticket. '
                                   'If this is a Wiley or OUP record, please map it manually to a Zendesk by adding '
                                   'it to manual_title2zd_dict.')
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
                                logger.warning('{} in output_dict will be overwritten by data in zd_dict'.format(fn))
                        except KeyError:
                            warning = 1
                if warning == 1:
                    logger.warning('{} not in zd_dict. This is probably because the zd number for this article was '
                                   'obtained from manual_title2zd_dict rather than from zd_dict and either (1) '
                                   'the zd ticket is newer than the zd export used here (using a new export should '
                                   'solve the problem); or (2) this zd_number is a '
                                   'typo in manual_title2zd_dict'.format(zd_number))
                    zd_number = ''
                if zd_number:
                    if reporttype == 'RCUK':
                        policy_flag = "RCUK policy [flag]"
                        payment_flag = "RCUK payment [flag]"
                    elif reporttype == 'COAF':
                        policy_flag = "COAF policy [flag]"
                        payment_flag = "COAF payment [flag]"
                    elif reporttype == 'ALL':
                        row[rejection_reason_field] = 'Included in output_dict by function import_prepayment_data; ' \
                                                      'report type is ALL)'
                        output_dict[publisher_id] = row
                        rejection_dict[publisher_id] = row  # this can be removed from the if statement as it also appears in else; leaving it here for now as still in active development
                        continue

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
        if request_status in ['Cancelled', 'Rejected', 'Denied', 'Reclaimed']:
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
    '''
    THIS FUNCTION IS PROBABLY OBSOLETE NOW. action_populate_report_fields() HAS TAKEN OVER ALL OF ITS FUNCTIONALITY.
    LEAVING IT HERE FOR NOW JUST IN CASE
    :param datasource_dict:
    :param translation_dict:
    :param default_publisher:
    :param default_pubtype:
    :param default_deal:
    :param default_notes:
    :return:
    '''
    temp_dict = {}
    for ticket in datasource_dict:
        for rep_f in translation_dict:
            for zd_f in translation_dict[rep_f]:
                if (rep_f not in datasource_dict[ticket].keys()) and (zd_f in datasource_dict[ticket].keys()):
                    #print('datasource_dict[ticket][zd_f]:', datasource_dict[ticket][zd_f])
                    if datasource_dict[ticket][zd_f]: #avoids AttributeError due to NoneType objects
                        if not datasource_dict[ticket][zd_f].strip() in ['-', 'unknown']: #ZD uses "-" to indicate NA #cottagelabs uses "unknown" to indicate NA for licence 
                            datasource_dict[ticket][rep_f] = datasource_dict[ticket][zd_f]
                            # datasource_dict[ticket][rep_f] = datasource_dict[ticket][zd_f] + ' | ' + zd_f ##USE THIS IF YOU NEED TO FIND OUT WHERE EACH BIT OF INFO IS COMING FROM
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
            oa_number = row['#externalID [txt]']
            article_title = row['#Manuscript title [txt]']
    #        rcuk_payment = row['RCUK payment [flag]']
    #        rcuk_policy = row['RCUK policy [flag]']
    #        apc_payment = row['Is there an APC payment? [list]']
    #        green_version = 'Green allowed version [list]'
    #        embargo = 'Embargo duration [list]'
    #        green_licence = 'Green licence [list]',
            apollo_handle = row['#Repository link [txt]'].replace('https://www.repository.cam.ac.uk/handle/' , '')
            doi = prune_and_cleanup_string(row['#DOI (like 10.123/abc456) [txt]'], DOI_CLEANUP, DOI_FIX)
            row['#DOI (like 10.123/abc456) [txt]'] = doi
            try:
                dateutil_options = dateutil.parser.parserinfo(dayfirst=True)
                publication_date = convert_date_str_to_yyyy_mm_dd(row['#Publication date (YYYY-MM-DD) [txt]'], dateutil_options)
                row['#Publication date (YYYY-MM-DD) [txt]'] = publication_date
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


def action_index_zendesk_data():
    '''
    This function reads in data exported from Zendesk and parses it into a number of global
    dictionaries. Zendesk tickets with the 'Duplicate' field set to 'yes' are ignored.

    :return:
    '''
    with open(zenexport, encoding = "utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # ignore any tickets in the groups below
            if row['Group'] in ['Cron Jobs', 'Request a Copy']:
                continue
            zd_number = row['Id']
            dup_of = row['Duplicate of (ZD-123456) [txt]']
            # excluding duplicates is a bad idea because several payments were made agains duplicates
            # if (row['Duplicate [flag]'] in ['no', '-', '']) or (zd_number in manual_zendesk_duplicates_to_include):
            if True:
                oa_number = row['#externalID [txt]']
                # logger.debug('ZD number {} has #externalID [txt] {}'.format(zd_number, oa_number))
                article_title = row['#Manuscript title [txt]'].upper()
                rcuk_payment = row['RCUK payment [flag]']
                rcuk_policy = row['RCUK policy [flag]']
                coaf_payment = row['COAF payment [flag]']
                coaf_policy = row['COAF policy [flag]']
        #        apc_payment = row['Is there an APC payment? [list]']
        #        green_version = 'Green allowed version [list]'
        #        embargo = 'Embargo duration [list]'
        #        green_licence = 'Green licence [list]',
                apollo_handle = row['#Repository link [txt]'].replace('https://www.repository.cam.ac.uk/handle/' , '')
                doi = prune_and_cleanup_string(row['#DOI (like 10.123/abc456) [txt]'], DOI_CLEANUP, DOI_FIX)
                row['#DOI (like 10.123/abc456) [txt]'] = doi
                dateutil_options = dateutil.parser.parserinfo(dayfirst=True)
                publication_date = convert_date_str_to_yyyy_mm_dd(row['#Publication date (YYYY-MM-DD) [txt]'], dateutil_options)
                row['#Publication date (YYYY-MM-DD) [txt]'] = publication_date
                if article_title not in ['', '-']:
                    if article_title in title2zd_dict.keys():
                        title2zd_dict[article_title].append(zd_number)
                    else:
                        title2zd_dict[article_title] = [zd_number]
                if doi not in ['', '-']:
                    if (doi in doi2zd_dict.keys()) and doi2zd_dict[doi]: ## Although we excluded tickets marked as duplicates from this loop, it is still possible to have unmarked duplicates reaching this line because of tickets that have not been processed yet by the OA team and/or errors
                        # print('zd_number:', zd_number)
                        # print('DOI:', doi)
                        # print('doi2zd_dict[doi]:', doi2zd_dict[doi])
                        # print('doi2zd_dict:', doi2zd_dict)
                        doi2zd_dict[doi].append(zd_number)
                    else:
                        doi2zd_dict[doi] = [zd_number]
                oa2zd_dict[oa_number] = zd_number
                apollo2zd_dict[apollo_handle] = zd_number
                zd2zd_dict[zd_number] = zd_number
                zd_dict[zd_number] = row
                if (rcuk_payment == 'yes') or (rcuk_policy == 'yes'):
                    zd_dict_RCUK[zd_number] = row
                    title2zd_dict_RCUK[article_title.upper()] = zd_number
                if (coaf_payment == 'yes') or (coaf_policy == 'yes'):
                    zd_dict_COAF[zd_number] = row
                    title2zd_dict_COAF[article_title.upper()] = zd_number
            else:
                if dup_of not in ['', '-']:
                    zd2oa_dups_dict[zd_number] = dup_of
                else:
                    pass # maybe capture these 'duplicates of empty string' somewhere

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

def action_populate_report_fields(reporting_dict, translation_dict, default_publisher = '', default_pubtype = '',
                                  default_deal = '', default_notes = ''):
    '''
    This function populates in the reporting dictionary the data fields that will be used in the output report

    :param reporting_dict: the reporting dictionary
    :param translation_dict: a dictionary mapping report fields to data source fields
    :param default_publisher: used for prepayment deals; if set, publisher will be set to this value
    :param default_pubtype: used for prepayment deals; if set, pubtype will be set to this value
    :param default_deal: used for prepayment deals; if set, deal will be set to this value
    :param default_notes: used for prepayment deals; if set, notes will be set to this value
    :return: the reporting dictionary populated with data from several sources
    '''
    rep_fund_field_list = ['Fund that APC is paid from (1)', 'Fund that APC is paid from (2)', 'Fund that APC is paid from (3)']

    zd_fund_field_list = ['RCUK payment [flag]', 'COAF payment [flag]', 'Other institution payment [flag]',
                          'Grant payment [flag]', 'Voucher/membership/offset payment [flag]',
                          'Author/department payment [flag]', #'Wellcome payment [flag]',
                          'Wellcome Supplement Payment [flag]']

    rep_funders = ['Funder of research (1)', 'Funder of research (2)', 'Funder of research (3)']
    zd_allfunders = [ 'Wellcome Trust [flag]',
                      'MRC [flag]',
                      'Cancer Research UK [flag]',
                      'EPSRC [flag]',
                      'British Heart Foundation [flag]',
                      'BBSRC [flag]',
                      'Arthritis Research UK [flag]',
                      'STFC [flag]',
                      "Breast Cancer Now (Breast Cancer Campaign) [flag]", # used to be 'Breast Cancer Campaign [flag]',
                      "Parkinson's UK [flag]",
                      'ESRC [flag]',
                      'Bloodwise (Leukaemia & Lymphoma Research) [flag]',
                      'NERC [flag]',
                      'AHRC [flag]',
                      'ERC [flag]', 'FP7 [flag]', 'NIHR [flag]', 'H2020 [flag]', 'Gates Foundation [flag]',
                      ]

    rep_grants = ['Grant ID (1)', 'Grant ID (2)', 'Grant ID (3)']
    zd_grantfields = ['COAF Grant Numbers [txt]'] #ZD funders field could also be used, but it does not seem to be included in the default export; this could be because it is a "multi-line text field" 

    for k, ticket in reporting_dict.items():
        ##DEAL WITH THE EASY FIELDS FIRST (ONE TO ONE CORRESPONDENCE)
        for rep_f in translation_dict:
            for zd_f in translation_dict[rep_f]:
                # if (rep_f not in ticket.keys()) and (zd_f in ticket.keys()): # this saves some time, but it means that info can come from fields that are not intended
                if zd_f in ticket.keys():
                    if ticket[zd_f]: #avoids AttributeError due to NoneType objects
                        if not ticket[zd_f].strip( ) in ['-', 'unknown']: #ZD uses "-" to indicate NA #cottagelabs uses "unknown" to indicate NA for licence
                            # convert dates to YYYY-MM-DD format
                            if (rep_f in ['Date of APC payment', 'Date of publication']) and (default_publisher == 'Wiley'):
                                ticket[zd_f] = convert_date_str_to_yyyy_mm_dd(ticket[zd_f])
                            ticket[rep_f] = ticket[zd_f]
                            # ticket[rep_f] = ticket[zd_f] + ' | ' + zd_f ##USE THIS IF YOU NEED TO FIND OUT WHERE EACH BIT OF INFO IS COMING FROM
        ##THEN WITH THE CONDITIONAL FIELDS
        ticket = process_repeated_fields(zd_fund_field_list, rep_fund_field_list, ticket)
        ticket = process_repeated_fields(zd_allfunders, rep_funders, ticket)
        ticket = process_repeated_fields(zd_grantfields, rep_grants, ticket)

        if default_publisher:
            ticket['Publisher'] = default_publisher
        if default_pubtype:
            ticket['Type of publication'] = default_pubtype
        if default_deal:
            ticket['Discounts, memberships & pre-payment agreements'] = default_deal
        # add GBP as currency for Wiley
        if default_publisher == 'Wiley':
            ticket['Currency of APC'] = 'GBP'
        # add discount value to notes
        if 'Prepayment discount' in ticket.keys():
            ticket['Notes'] = 'Prepayment discount: {}'.format(ticket['Prepayment discount'])
        elif default_notes:
            ticket['Notes'] = default_notes

        reporting_dict[k] = ticket

    return reporting_dict

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
zd_number_typos = {'30878':'50878',
                   '106512':'109512',
                   '116243':'119243',
                   '164388':'164338'
                   }
oa_number_typos = {'OA 10768':'OA 10468'}
description2zd_number = {
    "OPEN ACCESS FOR R DERVAN'S ARTICLE 'ON K-STABILITY OF FINITE COVERS' IN THE LMS BULLETIN" : '16490',
    'REV CHRG/ACQ TAX PD 04/16;  INV NO:Polymers-123512SUPPLIER:  MDPI AG' : '15589',
    'REV CHARGE AUG17  Supplier:  MDPI AG   Inv no:  remotesensing-207827' : '105991',
    'Rev chrg Dec 17  Supplier:  MDPI AG   Inv no:  ijerph-227528' : '138201',
    'Rev chrg Nov 17  Supplier:  MDPI AG   Inv no:  ijerph-210685' : '128036',
    'Rev chrg Jan 18  Supplier:  MDPI AG   Inv no:  jdb-242384' : '146827',
    'Rev chrg Jan 18  Supplier:  MDPI AG   Inv no:  water-235278' : '146445',
    'Rev chrg Jan 18  Supplier:  PUBLIC LIBRARY OF SCIENCE   Inv no:  PAB214162' : '153727',
    'PARTIAL REFUND FOR INVOICE 8085013' : '118609',
    'PARTIAL REFUND FOR INVOICE 1227288' : '156223',
    'Rev chrg Feb 18  Supplier:  THE JAPAN SOCIETY OF APPLIED PHYSICS   Inv no:  20171061P' : '143646',
    'Rev chrg Feb 18  Supplier:  THE JAPAN SOCIETY OF APPLIED PHYSICS   Inv no:  20176389' : '143646',
    'REV CHARGE Pd07/17  Supplier:  IVYSPRING INTERNATIONAL PUBLISHER   Inv no:  19841M2' : '87254',
    'REV CHARGE Pd07/17  Supplier:  MDPI AG   Inv no:  MICROMACHINES-206199' : '96070',
    'REV CHARGE Pd07/17  Supplier:  MDPI AG   Inv no:  materials-188050' : '86954',
    'REV CHARGE Pd07/17  Supplier:  MDPI AG   Inv no:  materials-191161' : '87223',
}
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
    '94189700 BANKCHRG' : '47567',
    ##INPUT FOR RCUK 2018 REPORT
    'materias-191161' : '87223',
    'materias-191161/BANK CHARGE' : '87223',
    'materials-191161' : '87223',
    'materials-191161/BANK CHARGE' : '87223',
    'materials-188050' : '86954',
    'materials-188050/ BK CHARGE' : '86954',
    '19841M2/ BK CHRG' : '87254',
    'MICROMACHINES-206199' : '96070',
    'MICROMACHINES-206199/BANK CHARGE' : '96070',
    '95319/CR' : '46300',
    '20170720' : '98467', # ACS Membership originally linked to ZD-88325; however, it makes more sense to link it to ZD-98467
    '20170524' : '81146',
}

lf = os.path.dirname(os.path.realpath(__file__))
os.chdir(lf)

# SETUP REPORT
reporttype = "RCUK" #Report requester. Supported values are: RCUK, COAF, ALL
rcuk_paydate_field = 'Posted' #Name of field in rcuk_paymentsfile containing the payment date
rcuk_payamount_field = 'Amount' #Name of field in rcuk_paymentsfile containing the payment amount
total_rcuk_payamount_field = 'RCUK APC Amount' #Name of field we want the calculated total RCUK APC to be stored in
coaf_paydate_field = 'GL Posting Date' #Name of field in coaf_last_year and coaf_this_year containing the payment date
coaf_payamount_field = 'Burdened Cost' #Name of field in coaf_last_year and coaf_this_year containing the payment date
total_coaf_payamount_field = 'COAF APC Amount' #Name of field we want the calculated total COAF APC to be stored in
total_apc_field = 'Total APC amount'

if reporttype in ["RCUK", "ALL"]:
    paydate_field = rcuk_paydate_field
    payamount_field = rcuk_payamount_field
    total_payamount_field = total_rcuk_payamount_field
    other_funder = "COAF"
    of_payamount_field = coaf_payamount_field
    total_of_payamount_field = total_coaf_payamount_field
    outputfile = os.path.join(working_folder, "{}_report_draft.csv".format(reporttype))
    outputgreen = os.path.join(working_folder, "{}_report_draft-green_papers.csv".format(reporttype))
    excluded_recs_logfile = os.path.join(working_folder, "{}_report_excluded_records.csv".format(reporttype))
elif reporttype == "COAF":
    paydate_field = coaf_paydate_field
    payamount_field = coaf_payamount_field
    total_payamount_field = total_coaf_payamount_field
    other_funder = "RCUK"
    of_payamount_field = rcuk_payamount_field
    total_of_payamount_field = total_rcuk_payamount_field
    outputfile = os.path.join(working_folder, "COAF_report_draft.csv")
    outputgreen = os.path.join(working_folder, "COAF_report_draft-green_papers.csv")
    excluded_recs_logfile = os.path.join(working_folder, "COAF_report_excluded_records.csv")
else:
    print("ERROR: Could not determine report requester (RCUK or COAF)")
    raise

with open(logfile, 'w') as log:
    log.write('APC Reporting Tool log of last run\n')

doifile = os.path.join(working_folder, "DOIs_for_cottagelabs.csv")
# RCUK GRANT REPORTS FROM CUFS
# rcuk_veje = os.path.join(working_folder, "VEJE_2017-10-31.csv")
# rcuk_veji = os.path.join(working_folder, "VEJI_2017-10-31_Jan2017_to_Mar2017.csv")
# rcuk_vejj = os.path.join(working_folder, "VEJI_and_VEJJ_1_April_2017_to_31_March_2018_290518.csv")
rcuk_vejx = os.path.join(working_folder, "RCUK_2018-08-09_all_VEJx_codes.csv")
# rcuk_paymentsfilename = "RCUK_merged_payments_file.csv"
rcuk_paymentsfilename = "UKRI-054_expenditures-detail_2019-04-30.csv"
rcuk_paymentsfile = os.path.join(working_folder, rcuk_paymentsfilename)
# merge_csv_files([rcuk_vejx, rcuk_veag054], rcuk_paymentsfile)
rcuk_veag054 = os.path.join(working_folder, "RCUK_VEAG054_2018-08-09.csv") # this sheet has the same format as COAF ones
rcuk_paymentsfile_veag = os.path.join(working_folder, rcuk_veag054)

# # COAF GRANT REPORTS FROM CUFS
# coaf_veag044 = os.path.join(working_folder, 'VEAG044_2018-08-09.csv')
# coaf_veag045 = os.path.join(working_folder, 'VEAG045_2018-08-09.csv')
# coaf_veag050 = os.path.join(working_folder, 'VEAG050_2018-08-09_with_resolved_journals.csv')
# coaf_veag052 = os.path.join(working_folder, 'VEAG052_2018-08-09.csv')
coaf_paymentsfilename = "COAF-055_expenditures-detail_2019-04-30.csv"
# coaf_paymentsfilename = "VEAG050_2018-08-09_with_resolved_journals.csv"
coaf_paymentsfile = os.path.join(working_folder, coaf_paymentsfilename)
# merge_csv_files([coaf_veag044, coaf_veag045, coaf_veag050, coaf_veag052], coaf_paymentsfile)

# METADATA SOURCES
zenexport = os.path.join(working_folder, "export-2019-04-30-0958-234063-36000492035352a6_filtered_groups.csv")
zendatefields = os.path.join(working_folder, "rcuk-report-active-date-fields-for-export-view-2017-11-13-2307.csv")
apolloexport = os.path.join(working_folder, "Apollo_all_items_2019-04-30.csv")
# instead of running results via Cottage Labs, let's use PMID-PMCID-DOI mappings available from
# https://europepmc.org/downloads
europepmc_map = os.path.join(working_folder, "PMID_PMCID_DOI.csv")
cottagelabsDoisResult = os.path.join(working_folder, "DOIs_for_cottagelabs_results.csv")
cottagelabsTitlesResult =  os.path.join(working_folder, "Titles_for_cottagelabs_2017-11-21_results_edited.csv")
cottagelabsexport = os.path.join(working_folder, "Cottagelabs_results.csv")
# merge_csv_files([cottagelabsDoisResult, cottagelabsTitlesResult], cottagelabsexport)
# merge_csv_files([cottagelabsDoisResult], cottagelabsexport)

# PREPAYMENT ACCOUNTS REPORTS
# springercompact_last_year = "Springer_Compact-December_2016_Springer_Compact_Report_for_UK_Institutions.csv"
# springercompact_this_year = "Springer_Compact-March_2017_Springer_Compact_Report_for_UK_Institutions.csv"
springercompactexport = os.path.join(working_folder, "Springer_Compact_article_approval_2018-04-01_to_2019-03-31.csv")
# merge_csv_files([springercompact_last_year, springercompact_this_year], springercompactexport)
wileyrcukcoaf = os.path.join(working_folder, "Wiley_RCUK-COAF_article_approval_2018-04-01_to_2019-03-31.csv")
wileycredit = os.path.join(working_folder, "Wiley_CREDIT_article_approval_2018-04-01_to_2019-03-31.csv")
wileyexport = os.path.join(working_folder, "Wiley_all_accounts.csv")
merge_csv_files([wileyrcukcoaf, wileycredit], wileyexport)
oupexport = os.path.join(working_folder, "OUP_OA_Charge_Data.csv")

# SETUP REPORT
report_template = os.path.join(working_folder, "Jisc_template_v4.csv")
report_start_date = datetime.datetime(2018, 4, 1) #(2016, 10, 1) COAF
report_end_date = datetime.datetime(2019, 3, 31, hour = 23, minute = 59, second = 59) #(2017, 9, 30, hour = 23, minute = 59, second = 59) COAF
green_start_date = datetime.datetime(2018, 4, 1)#Using 1 Jan to 31 Dec for green compliance estimate to match WoS period
green_end_date = datetime.datetime(2019, 3, 31, hour = 23, minute = 59, second = 59)

unmatched_payment_file_prefix = 'ART_debug_payments_not_matched_to_zd_numbers__'
nonJUDB_payment_file_prefix = 'ART_debug_non_JUDB_payments__'
nonEBDU_payment_file_prefix = 'ART_debug_non_EBDU_EBDV_or_EBDW_payments__'

###MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS IN zd_dict
rep2zd = [
('Date of acceptance', ['Symplectic acceptance date (YYYY-MM-DD) [txt]', 'Acceptance date', 'dcterms.dateAccepted']),
('PubMed ID', ['PMID']), #from cottagelabs or Europe PMC map
('DOI', ['#DOI (like 10.123/abc456) [txt]', 'rioxxterms.versionofrecord']),#, 'dc.identifier.uri']), #dc.identifier.uri often contains DOIs that are not in rioxxterms.versionofrecord, but it needs cleaning up (e.g. http://dx.doi.org/10.1111/oik.02622,https://www.repository.cam.ac.uk/handle/1810/254674 ); use only if the DOI cannot be found elsewhere
('Publisher', ['Publisher [txt]', 'dc.publisher']),
('Journal', ['#Journal title [txt]', 'prism.publicationName']),
('E-ISSN', ['ISSN']), #from cottagelabs
('Type of publication', ['#Symplectic item type [txt]', 'dc.type']),
('Article title', ['#Manuscript title [txt]', 'dc.title']),
('Date of publication', ['#Publication date (YYYY-MM-DD) [txt]', 'dc.date.issued']),
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
    'Breast Cancer Now (Breast Cancer Campaign) [flag]' : 'Breast Cancer Campaign',
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

    logfilename = os.path.join(working_folder, 'art_logging.log')

    logging.config.fileConfig('logging.conf', defaults={'logfilename': logfilename})
    logger = logging.getLogger('art')

    parse_invoice_data = False
    parse_springer_compact = True
    parse_wiley_dashboard = False
    parse_oup_prepayment = False
    estimate_green_compliance = False
    list_green_papers = False
    resolve_pmc_id = False

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
    if parse_springer_compact:
        springerfieldnames = extract_csv_header(springercompactexport, enc="utf-8", delim=';')
    if parse_wiley_dashboard:
        wileyfieldnames = extract_csv_header(wileyrcukcoaf, "utf-8")
    if parse_oup_prepayment:
        oupfieldnames = extract_csv_header(oupexport, "utf-8")
    rejection_reason_field = 'Reason for exclusion'

    allfieldnames = zendeskfieldnames + zendatefieldnames + rcuk_paymentsfieldnames + apollofieldnames + coaffieldnames
    # allfieldnames += cottagelabsfieldnames + springerfieldnames + wileyfieldnames + oupfieldnames


    #~ #pprint(allfieldnames)
    #~ #raise

    ##CLEANUP DEBUG INFO FROM PREVIOUS RUNS BY WRITING HEADERS
    logger.info('Cleanning up debug info from previous run')
    action_cleanup_debug_info()

    ###INDEX INFO FROM ZENDESK ON ZD NUMBER
    logger.info('Indexing zendesk info on zd number')
    action_index_zendesk_data()

    ### POPULATE doi2apollo DICTIONARY
    logger.info('Populating doi2apollo dictionary')
    action_populate_doi2apollo(apolloexport)

    #### PLUGGING IN DATA FROM ZENDESK DATE FIELDS
    logger.info('Plugging in data from zendesk date fields into zd_dict')
    plug_in_metadata(zendatefields, 'id', zd2zd_dict)

    #### PLUGGING IN DATA FROM THE RCUK AND COAF PAYMENTS SPREADSHEETS
    if parse_invoice_data:
        plug_in_payment_data(rcuk_paymentsfile, rcuk_paymentsfieldnames, 'Description', total_rcuk_payamount_field,
                             'Page, colour or membership amount', amount_field = rcuk_payamount_field,
                             file_encoding = 'utf-8', transaction_code_field = 'Tran', funder='RCUK')

        plug_in_payment_data(rcuk_paymentsfile_veag, coaffieldnames, 'Comment', total_rcuk_payamount_field,
                             'Page, colour or membership amount', invoice_field = 'Invoice',
                             amount_field = coaf_payamount_field, file_encoding = 'utf-8', funder='RCUK')
        plug_in_payment_data(coaf_paymentsfile, coaffieldnames, 'Comment', total_coaf_payamount_field,
                             'COAF Page, colour or membership amount', invoice_field = 'Invoice',
                             amount_field = coaf_payamount_field, file_encoding = 'utf-8', funder='COAF')

    #### PLUGGING IN DATA FROM APOLLO
    ###NEED TO MAP THIS DATA USING REPOSITORY HANDLE, BECAUSE APOLLO DOES
    ###NOT STORE ZD AND OA NUMBERS FOR ALL SUBMISSIONS
    logger.info('Plugging in data from Apollo into zd_dict')
    plug_in_metadata(apolloexport, 'handle', apollo2zd_dict)

    #### PLUGGING IN DATA FROM EUROPE PMC
    if resolve_pmc_id:
        logger.info('Plugging in data from Europe PMC into zd_dict')
        plug_in_metadata(europepmc_map, 'DOI', doi2zd_dict)

    # #### PLUGGING IN DATA FROM COTTAGELABS
    # ## For some reason not all PMIDs are appearing in the final COAF 2017 report, so this is something that needs to be fixed.
    # try:
    #     plug_in_metadata(cottagelabsexport, 'DOI', doi2zd_dict)
    # except FileNotFoundError:
    #     plog('WARNING: Compliance data from Cottage Labs not found; I will assume this is because it was not generated yet',
    #          terminal=True)

    #### MAUALLY FIX SOME PROBLEMS
    zd_dict['3743']['DOI'] = '10.1088/0953-2048/27/8/082001'
    zd_dict['3743']['#externalID [txt]'] = 'OA-1128'
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

    included_in_report = {}
    report_fields = extract_csv_header(report_template, "utf-8")
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
    report_fieldnames = report_fields + custom_rep_fields  # + rcuk_paymentsfieldnames
    #    report_fieldnames = report_fields ###UNCOMMENT THIS LINE FOR FINAL VERSION
    report_dict = {}
    if parse_invoice_data:
        #### NOW THAT WE PLUGGED IN ALL DATA SOURCES INTO THE ZENDESK EXPORT,
        #### PRODUCE THE FIRST PART OF THE REPORT (PAYMENTS LINKED TO ZENDESK)

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
        report_dict = action_populate_report_fields(report_dict, rep2zd)

        excluded_recs = {}

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

    #### LIST GREEN PAPERS
    if list_green_papers or estimate_green_compliance:
        ## TAKE A SAMPLE OF ZD TICKETS CREATED DURING REPORTING PERIOD, COVERED BY THE RCUK POLICY
        ### EXCLUDE ZD TICKETS MARKED AS DUPLICATES AND 'APC ALREADY PAID?'
        rcuk_dict = {}
        for a in zd_dict:
            row = zd_dict[a]
            rcuk_policy = row['RCUK policy [flag]']
            apc_already_paid = row['APC already paid? [flag]']
            ticket_creation = dateutil.parser.parse(row['Created at'])
            dup = row['Duplicate [flag]']
            apc_payment = row['Is there an APC payment? [list]']
            apc_payment_values = ['Yes', 'Wiley Dashboard', 'OUP Prepayment Account', 'Springer Compact',
                                  'Frontiers Institutional Account']
            if (rcuk_policy == 'yes') and (dup != 'yes') and (apc_already_paid != 'yes') and (
                apc_payment not in apc_payment_values) and (report_start_date <= ticket_creation <= report_end_date):
                rcuk_dict[a] = zd_dict[a]
        ## CHECK AND OUTPUT THOSE THAT ARE NOT MARKED AS NEEDING A PAYMENT
        # Workaround to obtain valid output using report_fieldnames
        report_dict = rcuk_dict
        report_dict = action_populate_report_fields(report_dict, rep2zd)
        # End of Workaround to obtain valid output using report_fieldnames
        ## INCLUDE ONLY ITEMS PUBLISHED SINCE 2016
        rcuk_recent_dict = {}
        for a in report_dict:
            row = report_dict[a]
            if row['Date of publication'].strip():
                publication_date = dateutil.parser.parse(row['Date of publication'])
                if publication_date >= datetime.datetime(2016, 1, 1):
                    rcuk_recent_dict[a] = report_dict[a]
            else:
                rcuk_recent_dict[a] = report_dict[a]
        plog('STATUS: Listing green papers', terminal=True)
        with open(outputgreen, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
            writer.writeheader()
            green_counter = 0
            for a in rcuk_recent_dict:
                writer.writerow(rcuk_recent_dict[a])
                green_counter += 1
        plog('STATUS: number of papers complying via the green route:', terminal=True)
        plog(str(green_counter), terminal=True)

    #### ESTIMATE COMPLIANCE VIA GREEN ROUTE ## this is the old method, used before 2018 reports
    if estimate_green_compliance:
        plog('STATUS: estimating compliance via the green route', terminal=True)
        ### TAKE A SAMPLE OF OUTPUTS COVERED BY THE RCUK POLICY AND PUBLISHED DURING THE REPORTING PERIOD
        ### EXCLUDE ZD TICKETS MARKED AS DUPLICATES OR "WRONG VERSION"
        rcuk_dict = {}
        for a in zd_dict:
            row = zd_dict[a]
            rcuk_policy = row['RCUK policy [flag]']
            ticket_creation = dateutil.parser.parse(row['Created at'])
            wrong_version = row['Wrong version [flag]']
            dup = row['Duplicate [flag]']
            if (rcuk_policy == 'yes') and (wrong_version != 'yes') and (dup != 'yes') and (
                    green_start_date <= ticket_creation <= green_end_date):
                rcuk_dict[a] = zd_dict[a]

        ## CHECK HOW MANY OF THOSE ARE GOLD, GREEN OR UNKNOWN
        green_dict = {}
        gold_dict = {}
        green_counter = 0
        gold_counter = 0
        WoS_total = 2580  # From Web of Science: number of University of Cambridge publications (articles, reviews and proceeding papers) acknowledging RCUK funding during the green reporting period
        for a in rcuk_dict:
            row = rcuk_dict[a]
            apc_payment = row['Is there an APC payment? [list]']
            green_version = row['Green allowed version [list]']
            embargo = row['Embargo duration [list]']
            green_licence = row['Green licence [list]']
            if apc_payment in apc_payment_values:
                gold_counter += 1
                gold_dict[a] = rcuk_dict[a]
            else:
                green_counter += 1
                green_dict[a] = rcuk_dict[a]

        rcuk_papers_total = gold_counter + green_counter

        plog('RESULT --- COMPLIANCE VIA GREEN/GOLD ROUTES:', terminal=True)
        plog(str(rcuk_papers_total),
             'ZD tickets covered by the RCUK open access policy were created during the green reporting period, of which:',
             terminal=True)
        plog(str(gold_counter), '(' + str(
            gold_counter / rcuk_papers_total) + ') tickets were placed in the GOLD route to comply with the policy',
             terminal=True)
        plog(str(green_counter), '(' + str(
            green_counter / rcuk_papers_total) + ') tickets were placed in the GREEN route to comply with the policy',
             terminal=True)
        plog('RESULT --- COMPLIANCE VIA GREEN/GOLD ROUTES AS A RATIO OF WoS TOTAL:', terminal=True)
        plog(str(WoS_total),
             'papers (articles, reviews and proceedings papers) acknowledging RCUK funding were published by the University of Cambridge during the green reporting period, of which:',
             terminal=True)
        plog(str(gold_counter / WoS_total), 'complied via the GOLD route', terminal=True)
        plog(str(green_counter / WoS_total), 'complied via the GREEN route', terminal=True)

    if (parse_springer_compact or parse_wiley_dashboard or parse_oup_prepayment) and not parse_invoice_data:
        # overwrite previous draft with report header
        with open(outputfile, 'w') as csvfile: #APPEND TO THE SAME OUTPUTFILE
            writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
            writer.writeheader()

    if parse_springer_compact:
        ### SPRINGER
        ### MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS
        rep2springer = [
        ('Date of acceptance', ['acceptance date']),
        ('PubMed ID', ['PMID']),  # NOT in prepayment dataset, but should be available from zd_dict
        ('DOI', ['#DOI (like 10.123/abc456) [txt]', 'rioxxterms.versionofrecord']), #('DOI', ['DOI']),
        #('Publisher', #NOT A VARIABLE; DEFAULT TO SPRINGER
        ('Journal', ['journal title']),
        ('E-ISSN', ['eISSN']),
        #('Type of publication', #NOT A VARIABLE; DEFAULT TO ARTICLE
        ('Article title', ['article title']),
        ('Date of publication', ['online first publication date', 'online issue publication date']),
        ('Date of APC payment', ['approval date']),
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
            ### RCUK REPORT 2018
            ## NOT FOUND IN ZENDESK
            '''Thermally-stable nanocrystalline steel''',
            '''Energy flows in the coffee plantations of Costa Rica: From traditional to modern systems (1935-2010)''',
            '''Harvesting the Commons''',
            '''Endoluminal vacuum therapy (E-Vac): a novel treatment option in oesophagogastric surgery''',
            '''The fate of the method of 'paradigms' in paleobiology''',
            '''Tracking Police Responses to “Hot” Vehicle Alerts: Automatic Number Plate Recognition and the Cambridge Crime Harm Index''',
            '''Reflections on and Extensions of the Fuller and Tabor Theory of Rough Surface Adhesion''',
            '''Sweet Spots for Hot Spots? A Cost-Effectiveness Comparison of Two Patrol Strategies''',
            '''Progressive multifocal leukoencephalopathy in the absence of immunosuppression''',
            '''Long-term changes in lowland calcareous grassland plots using Tephroseris integrifolia subsp. integrifolia as an indicator species.''',
            '''Biface knapping skill in the East African Acheulean: progressive trends and random walks''',
            '''Thermally-stable nanocrystalline steel''',
            '''Energy flows in the coffee plantations of Costa Rica: From traditional to modern systems (1935-2010)''',
            '''Harvesting the Commons''',
            '''Endoluminal vacuum therapy (E-Vac): a novel treatment option in oesophagogastric surgery''',
            '''The fate of the method of 'paradigms' in paleobiology''',
            '''Tracking Police Responses to “Hot” Vehicle Alerts: Automatic Number Plate Recognition and the Cambridge Crime Harm Index''',
            '''Reflections on and Extensions of the Fuller and Tabor Theory of Rough Surface Adhesion''',
            '''Sweet Spots for Hot Spots? A Cost-Effectiveness Comparison of Two Patrol Strategies''',
            '''Progressive multifocal leukoencephalopathy in the absence of immunosuppression''',
            '''Long-term changes in lowland calcareous grassland plots using Tephroseris integrifolia subsp. integrifolia as an indicator species.''',
            '''Biface knapping skill in the East African Acheulean: progressive trends and random walks''',
            ### RCUK REPORT 2019
            ## NOT FOUND IN ZENDESK
            '''Comparative quasi-static mechanical characterization of fresh and stored porcine trachea specimens''',
            '''State Failure, Polarisation, and Minority Engagement in Germany’s Refugee Crisis''',
            '''Tandem Androgenic and Psychological Shifts in Male Reproductive Effort Following a Manipulated "Win" or "Loss" in a Sporting Competition''',
            '''Pre-chamber ignition mechanism: simulations of transient autoignition in a mixing layer between reactants and partially-burnt products''',
            '''The Danish Crime Harm Index: How it Works and Why it Matters''',
            '''The First Metallurgy in the Pityusic Islands (Balearic Archipelago, Mediterranean Sea)''',
            '''On the Relations of the spaces A^p (Ω) and C^p (∂Ω)''',
            '''Mechanical support for high risk coronary artery bypass grafting''',
            '''Should we subtype ADHD according to the context in which symptoms occur? Criterion validity of context-based ADHD subtypes''',
            '''A mathematical model for velodrome cycling''',
            '''Laparoscopic adhesiolysis: not for all patients, not for all surgeons, not in all centers''',
            '''Severing telicity from result: on two types of resultative compound verb in Dongying Mandarin''',
            '''Predictors of early progression of surgically treated atypical meningiomas''',
            '''Emergence of novel phenomena on the border of low dimensional spin and charge order''',
        ]
        exclude_titles_springer = []
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

        springer_out_dict = action_populate_report_fields(springer_dict, rep2springer,
                                                                     'Springer', 'Article', 'Springer Compact',
                                                                     'Springer Compact')

        # add springer entries to report_dict so that they are included in the cottage labs file
        report_dict.update(springer_out_dict)

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

    if parse_wiley_dashboard:
        ### WILEY
        ###MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS
        rep2wiley = [
        ('Date of acceptance', ['Article Accepted Date']),
        ('PubMed ID', ['PMID']),  # NOT in prepayment dataset, but should be available from zd_dict
        ('DOI', ['Wiley DOI']),             ## Fields in Wiley report are 'DOI' and 'Publisher', but I had to append 'Wiley ' to these two lines
        ('Publisher', ['Wiley Publisher']), ## because ART has a mechanism that prevents existing fields (e.g. comming from zd) from being overwritten
        ('Journal', ['Journal']),           ## by data from prepayment deals; this is something that probably needs revising because it is confusing, not obvious
        ('E-ISSN', ['Journal Electronic ISSN']),
        ('Type of publication', ['Article Type']),
        ('Article title', ['Article Title']),
        ('Date of publication', ['EV Published Date']),
        ('Date of APC payment', ['Date']),
        ('APC paid (actual currency) excluding VAT', ['Withdrawals']),
        #('Currency of APC', #NA # All Wiley values are shown in GBP
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

        wiley_out_dict = action_populate_report_fields(wiley_dict, rep2wiley, 'Wiley', default_deal = 'Other', default_notes = 'Wiley prepayment discount')

        # add wiley entries to report_dict so that they are included in the cottage labs file
        report_dict.update(wiley_out_dict)

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

    if parse_oup_prepayment:
        ###OUP
        ###MAP REPORT FIELDS TO HARVESTED OR CALCULATED FIELDS
        rep2oup = [
        ('Date of acceptance', ['Accepted For Publication', 'Approved For Publication']),
        ('PubMed ID', ['PMID']), # NOT in OUP dataset, but should be available from zd_dict
        ('DOI', ['Doi']),
        #('Publisher', #NOT A VARIABLE; DEFAULT TO OUP
        ('Journal', ['Journal Name']),
        #('E-ISSN', ['eISSN']), #NA QUERY ORPHEUS?
        #('Type of publication', #NOT A VARIABLE; DEFAULT TO ARTICLE
        ('Article title', ['Manuscript Title']),
        ('Date of publication', ['Issue Online']),
        ('Date of APC payment', ['Order Date', 'Referral Date']),
        ('APC paid (actual currency) excluding VAT', ['Charge Amount']), #NA COULD BE CALCULATED
        ('Currency of APC', ['Currency']),
        #('APC paid (£) including VAT if charged', ['Charge Amount']), #NA
        #('Additional publication costs (£)', #NA
        #('Discounts, memberships & pre-payment agreements', #NOT A VARIABLE; DEFAULT TO OTHER
        #('Amount of APC charged to COAF grant (including VAT if charged) in £', #NA
        #('Amount of APC charged to RCUK OA fund (including VAT if charged) in £', #NA
        ('Licence', ['OUP Licence', 'Licence']),
        #('Notes', ['Comments']) #DEFAULT TO OUP PREPAYMENT DEAL 'Journal APC'
        ]
        rep2oup = collections.OrderedDict(rep2oup)

        oup_dict = {}
        rejection_dict_oup = {}
        dateutil_oup = dateutil.parser.parserinfo() # Used for RCUK report but no longer valid: dateutil.parser.parserinfo(dayfirst=True)
        filter_date_field_oup = 'Order Date' # 'Referral Date'
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

        oup_out_dict = action_populate_report_fields(oup_dict, rep2oup, 'Oxford University Press', 'Article', 'Other', 'Oxford University Press prepayment discount')

        # add oup entries to report_dict so that they are included in the cottage labs file
        report_dict.update(oup_out_dict)

        with open(outputfile, 'a') as csvfile: #APPEND TO THE SAME OUTPUTFILE
            writer = csv.DictWriter(csvfile, fieldnames=report_fieldnames, extrasaction='ignore')
            #~ writer.writeheader()
            for doi in oup_out_dict:
                if 'Date of acceptance' in oup_out_dict[doi].keys():
                    if oup_out_dict[doi]['Date of acceptance'].strip():
                        acceptance_date = dateutil.parser.parse(oup_out_dict[doi]['Date of acceptance'], dateutil_oup)
                        oup_out_dict[doi]['Date of acceptance'] = acceptance_date.strftime('%Y-%m-%d')
                if 'Date of publication' in oup_out_dict[doi].keys():
                    if oup_out_dict[doi]['Date of publication'].strip():
                        publication_date = dateutil.parser.parse(oup_out_dict[doi]['Date of publication'])
                        oup_out_dict[doi]['Date of publication'] = publication_date.strftime('%Y-%m-%d')
                if 'Date of APC payment' in oup_out_dict[doi].keys():
                    if oup_out_dict[doi]['Date of APC payment'].strip():
                        payment_date = dateutil.parser.parse(oup_out_dict[doi]['Date of APC payment'])
                        oup_out_dict[doi]['Date of APC payment'] = payment_date.strftime('%Y-%m-%d')
                writer.writerow(oup_out_dict[doi])

        plog('STATUS: Finished processing OUP Prepayment entries')

    # # NOW LET'S EXPORT A CSV OF DOIS TO UPLOAD TO https://compliance.cottagelabs.com
    # # FIX THIS ONE MANUALLY ON THE OUTPUT CSV: http:/​/​dx.​doi.​org/​10.​1104/​pp.​16.​00539
    # with open(doifile, 'w') as csvfile:
    #     writer = csv.DictWriter(csvfile, fieldnames=['DOI'], extrasaction='ignore')
    #     writer.writeheader()
    #     for ticket in report_dict:
    #         if 'DOI' in report_dict[ticket].keys():
    #             if report_dict[ticket]['DOI'].strip():
    #                 writer.writerow(report_dict[ticket])

