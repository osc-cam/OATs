#!/usr/bin/env python3

import os
import sys
import re
import shutil
import time
import subprocess

test_mode = 1

## Function plog is also used by art.py, so could be moved to a oats_common module
def plog(*args, logfile=os.path.splitext(os.path.realpath(__file__))[0] + '.log', terminal=True):
    '''
    A function to print arguments to a log file
    :param args: the arguments to output
    :param terminal: if set to false, suppresses terminal output
    '''
    with open(logfile, 'a') as f:
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

def oasis_copy(src, dst):
    if test_mode == 0:
        shutil.copy(src, dst)
    else:
        plog("OASIS TEST: Running in test mode\n", src, "was NOT COPIED to", dst)


def oasis_move(src, dst):
    if test_mode == 0:
        shutil.move(src, dst)
    else:
        plog("OASIS TEST: Running in test mode\n", src, "was NOT MOVED to", dst)


def setup_os(platform_string=sys.platform, home=os.path.expanduser("~")):
    pdftk = 'pdftk'
    username = home.split('/')[-1]
    rm_cmd = 'rm'
    if platform_string.startswith('linux'):
        open_cmd = 'xdg-open'
    elif platform_string.startswith('win32'):
        open_cmd = 'start'
        rm_cmd = 'del'
        username = home.split("\\")[-1]
        pdftk = os.path.join(oasisfolder, "pdftk\pdftk.exe")
    elif platform_string.startswith('darwin'):  # MAC OS
        open_cmd = 'open'
    else:
        plog('OASIS ERROR: Operational system', platform_string,
              'not supported. Oasis will attempt to apply linux parameters')
        open_cmd, username, pdftk = setup_os('linux')
    return (open_cmd, rm_cmd, username, home, pdftk)


# CUT OFF DATES FOR OLD INVOICE WARNING
cutoffyear = 2017
cutoffmonth = 8

# SET UP PROGRAM VARIABLES
open_cmd, rm_cmd, username, home, pdftk = setup_os()

# CHECK THAT PDFTK IS INSTALLED
try:
    subprocess.run(pdftk, stdout=open(os.devnull, 'w'), check=True)
except FileNotFoundError:
    sys.exit('ERROR: pdftk could not be found. Please make sure it is installed in your system.')

oasisfolder = os.path.dirname(os.path.realpath(__file__))  # the folder containing this script
os.chdir(oasisfolder)
config_folder = os.path.join(home, ".OATs", "OASIS")
configfile = os.path.join(config_folder, "config.txt")
configexample = r"""## UNIX
Browser download folder = /home/<your username>/Downloads
Path to shared OSC drive = /home/<your username>/OSC-shared-drive/OSC

## WINDOWS
Browser download folder = C:\userdata\<your CRSid>\downloads
Path to shared OSC drive = O:\OSC"""

warning_counter = 0

if not os.path.exists(config_folder):
    os.makedirs(config_folder)

if not os.path.exists(configfile):
    plog("OASIS: Configuration file does not exist. Creating and opening the file. Please edit the paths to match your system")
    f = open(configfile, 'w')
    f.write(configexample)
    f.close()
    subprocess.call([open_cmd, configfile])
    a = input("Have you finished editing the config file? (y/n)")
    while a not in ["y", "Y", "yes", "YES"]:
        if a == "q":
            sys.exit()
        a = input("Have you finished editing the config file? (y/n) (or q to quit)")

plog("OASIS: Reading configuration file.")

downloadsfolder = ''
shareddrive = ''
with open(configfile, 'r') as f:
    for line in f:
        configlist = line.split("=")
        if "BROWSER DOWNLOAD FOLDER" in configlist[0].upper():
            downloadsfolder = configlist[1].strip()
        if "PATH TO SHARED OSC DRIVE" in configlist[0].upper():
            shareddrive = configlist[1].strip()

if not os.path.exists(downloadsfolder):
    sys.exit("OASIS ERROR: 'Browser download folder' set in " + configfile + " does not exist. Please check")
if not os.path.exists(shareddrive):
    sys.exit("OASIS ERROR: 'Path to shared OSC drive' set in " + configfile + " is not reachable. Please check your connection")

remoteinvoicefolder = os.path.join(shareddrive, "PaymentsAndCommitments", "Invoices")
printfolder = os.path.join(remoteinvoicefolder, "Invoices_to_print")

invoicevarfile = os.path.join(config_folder, "invoice-variables.txt")
if not os.path.exists(invoicevarfile):
    with open(invoicevarfile, "w") as f:
        f.write("OVERWRITE THIS WITH INVOICE INFO COPIED AND PASTED FROM ZENDESK")
overlayfile = os.path.join(oasisfolder, "overlay.tex")
filingfolder = os.path.join(remoteinvoicefolder, "Invoices to be checked")

# GET RID OF TEMPORARY FILES FROM PREVIOUS RUN
plog("OASIS: Deleting temporary files from previous run")
os.system(rm_cmd + " tempinv*.pdf invoice.pdf doc_data.txt overlay.aux overlay.log overlay.synctex.gz")

# COPY THE INVOICE FROM DOWNLOADS TO LOCAL FOLDER
modtimes = []
for i in os.listdir(downloadsfolder):
    try:
        mod = os.path.getmtime(os.path.join(downloadsfolder, i))
        modtimes.append((mod, i))
    except FileNotFoundError:
        pass

modtimes.sort()
listcounter = -1
invoicefilename = modtimes[listcounter][1]
while invoicefilename[-4:].upper() not in [".PDF"]:
    listcounter = listcounter - 1
    invoicefilename = modtimes[listcounter][1]
invoicefile = os.path.join(oasisfolder, "invoice.pdf")
src = os.path.join(downloadsfolder, invoicefilename)
dst = invoicefile
shutil.copy(src, dst)

plog("OASIS: Copied the invoice file", invoicefilename, "to", oasisfolder)

# DETECT NUMBER OF PAGES AND SPLIT IF NECESSARY
process = subprocess.Popen([pdftk, invoicefile, "dump_data"], stdout=subprocess.PIPE)
out, err = process.communicate()
t = re.compile("NumberOfPages: [0-9]+")
m = t.search(str(out))
if m:
    nopages = int(m.group().replace("NumberOfPages: ", "").strip())
else:
    plog("WARNING: Failed to detect invoice number of pages. I will assume it contains only 1 page.")
    nopages = 1

# print "OASIS: This invoice has", str(nopages), "pages"
if nopages > 1:
    plog("OASIS: Splitting", str(nopages), "pages")
    subprocess.check_call([pdftk, invoicefile, "burst", "output", os.path.join(oasisfolder, "tempinv%02d.pdf")])
else:
    plog("OASIS: This invoice has only", str(nopages), "page\n")
    src = invoicefile
    dst = os.path.join(oasisfolder, "tempinv01.pdf")
    shutil.move(src, dst)

# SUMMON invoicevarfile AND overlayfile, THEN PROMPTS USER TO STAMP INVOICE
subprocess.run([open_cmd, invoicevarfile])
subprocess.run([open_cmd, overlayfile])

plog("OASIS: Please copy the invoice data to", invoicevarfile, "if you have not done so already")
plog("OASIS: Please stamp the invoice using TeXworks.\n")
a = input("After stamping the invoice, please close the preview TeXworks window.\nHave you finished stamping the invoice? (y/n)")
while a not in ["y", "Y", "yes", "YES"]:
    if a == "q":
        sys.exit()
    a = input("Have you finished stamping the invoice? (y/n) (or q to quit)")

# EXTRACT INVOICE DATE AND ADD WARNING ABOUT OLD INVOICE IF NEEDED
varinput = open(invoicevarfile, 'r')
varcontent = varinput.read()
varinput.close()
tinvdate = re.compile("INVOICE DATE: .+")
minvdate = tinvdate.search(varcontent)
if minvdate:
    oldinvwarn = False
    invdate = minvdate.group().replace("INVOICE DATE: ", "").strip()
    datelist = invdate.split('-')
    year = int(datelist[0])
    month = int(datelist[1])
    day = int(datelist[2])
    if year < cutoffyear:
        oldinvwarn = True
    elif (year == cutoffyear) and month < cutoffmonth:
        oldinvwarn = True
    if oldinvwarn:
        with open(invoicevarfile, 'a') as f:
            f.write('\n' + r'\renewcommand{\oldwarning}{\textbf{NOTE FOR MEL}: This is an old invoice.}')
else:
    plog("OASIS WARNING: Failed to extract invoice date from", invoicevarfile)
    warning_counter += 1

# REPLACE FIRST PAGE WITH STAMPED COPY
src = os.path.join(oasisfolder, "overlay.pdf")
dst = os.path.join(oasisfolder, "tempinv01.pdf")
oasis_copy(src, dst)

# MERGE PAGES AGAIN IF INVOICE HAS MORE THAN ONE PAGE OR RENAME 1 PAGE INVOICES
stampedinvoice = os.path.join(oasisfolder, "stamped_invoice.pdf")
if nopages > 1:
    plog("OASIS: Merging stamped page with remaining invoice pages")
    subprocess.check_call([pdftk, os.path.join(oasisfolder, "tempinv*.pdf"), "cat", "output", stampedinvoice])
else:
    src = os.path.join(oasisfolder, "tempinv01.pdf")
    dst = stampedinvoice
    oasis_copy(src, dst)

# OBTAIN INVOICE DATA AND RENAME THE FILE TO <OA/ZD NUMBER>_<INVOICE NUMBER>.PDF
plog("OASIS: Renaming invoice to <OA/ZD NUMBER>_<INVOICE NUMBER>.pdf")
invno = ""
tinvno = re.compile("%%%%INVOICE VARIABLES FOR .+%%%%")
minvno = tinvno.search(varcontent)
if minvno:
    invno = minvno.group().replace("%%%%INVOICE VARIABLES FOR ", "").replace("%%%%", "").replace("/", "").strip()
else:
    sys.exit("OASIS ERROR: Failed to extract invoice number from", invoicevarfile)

refno = ""
toa = re.compile("OA-[0-9]+")
tzd = re.compile("ZD-[0-9]+")

moa = toa.search(varcontent)
mzd = tzd.search(varcontent)
if moa:
    refno = moa.group()
elif mzd:
    refno = mzd.group()
else:
    refno = "REF-ERROR"
    sys.exit("OASIS ERROR: Failed to extract OA or ZD number from", invoicevarfile)

invfilename = refno + "_" + invno + ".pdf"
src = stampedinvoice
dst = os.path.join(oasisfolder, invfilename)
oasis_move(src, dst)

# COPY FILE TO PRINTFOLDERS AND FILE IT ON THE O: DRIVE
if invfilename not in os.listdir(printfolder):
    src = os.path.join(oasisfolder, invfilename)
    dst = os.path.join(printfolder, invfilename)
    oasis_copy(src, dst)
    plog("OASIS: copied stamped invoice to", printfolder)
else:
    msg = "Invoice " + invfilename + " already exists in " + printfolder
    overwrite = input("OASIS: " + msg + ". Would you like to overwrite it? (y/n)[n]")
    if overwrite in ["Y", 'y']:
        src = os.path.join(oasisfolder, invfilename)
        dst = os.path.join(printfolder, invfilename)
        oasis_copy(src, dst)
        plog("OASIS: copied stamped invoice to", printfolder)
    else:
        sys.exit("OASIS ERROR:", msg)

if invfilename not in os.listdir(filingfolder):
    src = os.path.join(oasisfolder, invfilename)
    dst = os.path.join(filingfolder, invfilename)
    oasis_move(src, dst)
    plog("OASIS: moved stamped invoice to", filingfolder)
else:
    msg = "Invoice " + invfilename + " already exists in " + filingfolder
    overwrite = input("OASIS: " + msg + ". Would you like to overwrite it? (y/n)[n]")
    if overwrite in ["Y", 'y']:
        src = os.path.join(oasisfolder, invfilename)
        dst = os.path.join(filingfolder, invfilename)
        oasis_move(src, dst)
        plog("OASIS: moved stamped invoice to", filingfolder)
    else:
        sys.exit("OASIS ERROR:", msg)

# WARN USER IF THERE ARE INVOICES THAT SHOULD BE PRINTED SOON
maxnoinvtoprint = 10
currentnoinvtoprint = len(list(filter(os.path.isfile, os.listdir(printfolder))))
if currentnoinvtoprint > maxnoinvtoprint:
    plog("WARNING: There are", str(currentnoinvtoprint), "invoices waiting to be printed in", printfolder)
    plog("Don't forget to print them at some point!")
    warning_counter += 1

maxprintdelaydays = 5
maxprintdelaysecs = maxprintdelaydays * 86400
printfoldermodtimes = []
for i in os.listdir(printfolder):
    if not os.path.isdir(os.path.join(printfolder, i)):
        mod = os.path.getmtime(os.path.join(printfolder, i))
        printfoldermodtimes.append((mod, i))

printfoldermodtimes.sort()
oldestinvoicemodtime = printfoldermodtimes[0][0]
oldestinvoicename = printfoldermodtimes[0][1]
timenow = time.time()
if oldestinvoicemodtime + maxprintdelaysecs < timenow:
    plog("WARNING:", oldestinvoicename, "is older than", str(maxprintdelaydays), "days")
    plog("Don't forget to print old invoices at some point!")
    warning_counter += 1

if warning_counter > 0:
    plog("\nOASIS: Processing finished with", warning_counter, "warnings.")
    plog("Please review the log above carefully for details")
else:
    plog("\nThank you for using the Open Access Service Invoice Stamper!")
