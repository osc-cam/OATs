import os
import re
import shutil
import time
import subprocess

test_mode = 0

def oasis_copy(src, dst):
    if test_mode == 0:
        shutil.copy(src, dst)
    else:
        print("OASIS TEST: Running in test mode\n", src, "was NOT COPIED to", dst)

def oasis_move(src, dst):
    if test_mode == 0:
        shutil.move(src, dst)
    else:
        print("OASIS TEST: Running in test mode\n", src, "was NOT MOVED to", dst)
        
#CUT OFF DATES FOR OLD INVOICE WARNING
cutoffyear = 2017
cutoffmonth = 8

#SET UP PROGRAM VARIABLES AND CHECK FOR UPDATES
home = os.path.expanduser("~")
userid = home.split("\\")[-1]

localfolder = os.path.dirname(os.path.realpath(__file__)) #the folder containing this script
os.chdir(localfolder)
internfolder = os.path.join(home, ".OATs", "OASIS")
configfile = os.path.join(internfolder, "config.txt")
configexample = r"""Browser download folder = C:\userdata\<your CRSid>\downloads
Path to shared OSC drive = O:\OSC"""

warning_counter = 0

if not os.path.exists(internfolder):
    os.makedirs(internfolder)

if not os.path.exists(configfile):
    print("OASIS: Configuration file does not exist. Creating and opening the file. Please edit the paths to match your system")
    f = open(configfile, 'w')
    f.write(configexample)
    f.close()
    os.system("start " + configfile)
    a = input("Have you finished editing the config file? (y/n)")
    while a not in ["y", "Y", "yes", "YES"]:
        if a == "q":
            raise
        a = input("Have you finished editing the config file? (y/n) (or q to quit)")

print("OASIS: Reading configuration file.")
f = open(configfile, 'r')
downloadsfolder = ''
shareddrive = ''
for line in f:
    configlist = line.split("=")
    if "BROWSER DOWNLOAD FOLDER" in configlist[0].upper():
        downloadsfolder = configlist[1].strip()
    if "PATH TO SHARED OSC DRIVE" in configlist[0].upper():
        shareddrive = configlist[1].strip()

if not os.path.exists(downloadsfolder):
    print("OASIS ERROR: 'Browser download folder' set in", configfile, "does not exist. Please check")
    raise
if not os.path.exists(shareddrive):
    print("OASIS ERROR: 'Path to shared OSC drive' set in", configfile, "is not reachable. Please check your connection")
    raise
    
remoteinvoicefolder = os.path.join(shareddrive, "PaymentsAndCommitments\Invoices")
printfolder = os.path.join(remoteinvoicefolder, "Invoices_to_print")

pdftk = os.path.join(localfolder, "pdftk\pdftk.exe")

#invoicefolder = os.path.join("h:", "finance", "emailed_invoices")
invoicefolder = localfolder
invoicevarfile = os.path.join(internfolder, "invoice-variables.txt")
if not os.path.exists(invoicevarfile):
    with open(invoicevarfile, "w") as f:
        f.write("OVERWRITE THIS WITH INVOICE INFO COPIED AND PASTED FROM ZENDESK")
overlayfile = os.path.join(invoicefolder, "overlay.tex")
filingfolder = os.path.join(remoteinvoicefolder, "Invoices to be checked")

#GET RID OF TEMPORARY FILES FROM PREVIOUS RUN
print("OASIS: Deleting temporary files from previous run")
os.system("del tempinv*.pdf invoice.pdf doc_data.txt overlay.aux overlay.log overlay.synctex.gz") #Windows version

#COPY THE INVOICE FROM DOWNLOADS TO LOCAL FOLDER
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
invoicefile = os.path.join(invoicefolder, "invoice.pdf")
src = os.path.join(downloadsfolder, invoicefilename)
dst = invoicefile
shutil.copy(src, dst)

print("OASIS: Copied the invoice file")
print("OASIS:", invoicefilename)
print("OASIS: to", invoicefolder)

#DETECT NUMBER OF PAGES AND SPLIT IF NECESSARY
process = subprocess.Popen([pdftk, invoicefile, "dump_data"], stdout=subprocess.PIPE)
out, err = process.communicate()
t = re.compile("NumberOfPages: [0-9]+")
m = t.search(str(out)) 
if m:
    nopages = int(m.group().replace("NumberOfPages: ", "").strip())
else:
    print("WARNING: Failed to detect invoice number of pages. I will assume it contains only 1 page.")
    nopages = 1

#print "OASIS: This invoice has", str(nopages), "pages"
if nopages > 1:
    print("OASIS: Splitting", str(nopages), "pages")
    subprocess.check_call([pdftk, invoicefile, "burst", "output", os.path.join(invoicefolder, "tempinv%02d.pdf")])
else:
    print("OASIS: This invoice has only", str(nopages), "page\n")
    src = invoicefile
    dst = os.path.join(invoicefolder, "tempinv01.pdf")
    shutil.move(src, dst)    
    
#SUMMON invoicevarfile AND overlayfile, THEN PROMPTS USER TO STAMP INVOICE
os.system("start " + invoicevarfile)
os.system("start " + overlayfile)

print("OASIS: Please copy the invoice data to", invoicevarfile, "if you have not done so already")
print("OASIS: Please stamp the invoice using TeXworks.\n")
a = input("After stamping the invoice, please close the preview TeXworks window.\nHave you finished stamping the invoice? (y/n)")
while a not in ["y", "Y", "yes", "YES"]:
    if a == "q":
        raise
    a = input("Have you finished stamping the invoice? (y/n) (or q to quit)")

#EXTRACT INVOICE DATE AND ADD WARNING ABOUT OLD INVOICE IF NEEDED
varinput = open(invoicevarfile, 'r')
varcontent = varinput.read()
varinput.close()
tinvdate = re.compile("INVOICE DATE: .+")
minvdate = tinvdate.search(varcontent)
if minvdate:
    oldinvwarn = False
    invdate = minvdate.group().replace("INVOICE DATE: ","").strip()
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
    print("OASIS WARNING: Failed to extract invoice date from", invoicevarfile)
    warning_counter += 1
    
#REPLACE FIRST PAGE WITH STAMPED COPY    
src = os.path.join(invoicefolder, "overlay.pdf")
dst = os.path.join(invoicefolder, "tempinv01.pdf")
oasis_copy(src, dst)

#MERGE PAGES AGAIN IF INVOICE HAS MORE THAN ONE PAGE OR RENAME 1 PAGE INVOICES
stampedinvoice = os.path.join(invoicefolder, "stamped_invoice.pdf")
if nopages > 1:
    print("OASIS: Merging stamped page with remaining invoice pages")
    subprocess.check_call([pdftk, os.path.join(invoicefolder, "tempinv*.pdf"), "cat", "output", stampedinvoice])
else:
    src = os.path.join(invoicefolder, "tempinv01.pdf")
    dst = stampedinvoice
    oasis_copy(src, dst)

#OBTAIN INVOICE DATA AND RENAME THE FILE TO <OA/ZD NUMBER>_<INVOICE NUMBER>.PDF
print("OASIS: Renaming invoice to <OA/ZD NUMBER>_<INVOICE NUMBER>.pdf")
invno = ""
tinvno = re.compile("%%%%INVOICE VARIABLES FOR .+%%%%")
minvno = tinvno.search(varcontent)
if minvno:
    invno = minvno.group().replace("%%%%INVOICE VARIABLES FOR ","").replace("%%%%","").replace("/","").strip()
else:
    print("OASIS ERROR: Failed to extract invoice number from", invoicevarfile)
    raise
    
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
    print("OASIS ERROR: Failed to extract OA or ZD number from", invoicevarfile)
    raise

invfilename = refno + "_" + invno + ".pdf"    
src = stampedinvoice
dst = os.path.join(invoicefolder, invfilename)
oasis_move(src, dst)

#COPY FILE TO PRINTFOLDERS AND FILE IT ON THE O: DRIVE
if invfilename not in os.listdir(printfolder):
    src = os.path.join(invoicefolder, invfilename)
    dst = os.path.join(printfolder, invfilename)
    oasis_copy(src, dst)
    print("OASIS: copied stamped invoice to", printfolder)
else:
    msg = "Invoice " + invfilename + " already exists in " + printfolder
    overwrite = input("OASIS: " + msg + ". Would you like to overwrite it? (y/n)[n]")
    if overwrite in ["Y", 'y']:
        src = os.path.join(invoicefolder, invfilename)
        dst = os.path.join(printfolder, invfilename)
        oasis_copy(src, dst)
        print("OASIS: copied stamped invoice to", printfolder)
    else:
        print("OASIS ERROR:", msg)
        raise

if invfilename not in os.listdir(filingfolder):
    src = os.path.join(invoicefolder, invfilename)
    dst = os.path.join(filingfolder, invfilename)
    oasis_move(src, dst)
    print("OASIS: moved stamped invoice to", filingfolder)
else:
    msg = "Invoice " + invfilename + " already exists in " + filingfolder
    overwrite = input("OASIS: " + msg + ". Would you like to overwrite it? (y/n)[n]")
    if overwrite in ["Y", 'y']:
        src = os.path.join(invoicefolder, invfilename)
        dst = os.path.join(filingfolder, invfilename)
        oasis_move(src, dst)
        print("OASIS: moved stamped invoice to", filingfolder)
    else:
        print("OASIS ERROR:", msg)
        raise
        
#WARN USER IF THERE ARE INVOICES THAT SHOULD BE PRINTED SOON    
maxnoinvtoprint = 10
currentnoinvtoprint = len(os.listdir(printfolder))
if currentnoinvtoprint > maxnoinvtoprint:
    print("WARNING: There are", str(currentnoinvtoprint), "invoices waiting to be printed in", printfolder)
    print("Don't forget to print them at some point!")
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
    print("WARNING:", oldestinvoicename, "is older than", str(maxprintdelaydays), "days")
    print("Don't forget to print old invoices at some point!")
    warning_counter += 1

if warning_counter > 0:
    print("\nOASIS: Processing finished with", warning_counter, "warnings.")
    print("Please review the log above carefully for details")
else:
    print("\nThank you for using the Open Access Service Invoice Stamper!")
