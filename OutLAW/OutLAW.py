import os
import re
import shutil
import time
import subprocess

test_mode = 0

def OutLAW_copy(src, dst):
    if test_mode == 0:
        shutil.copy(src, dst)
    else:
        print("OutLAW TEST: Running in test mode\n", src, "was NOT COPIED to", dst)

def OutLAW_move(src, dst):
    if test_mode == 0:
        shutil.move(src, dst)
    else:
        print("OutLAW TEST: Running in test mode\n", src, "was NOT MOVED to", dst)
        
#SET UP PROGRAM VARIABLES AND CHECK FOR UPDATES
home = os.path.expanduser("~")
userid = home.split("\\")[-1]

localfolder = os.path.dirname(os.path.realpath(__file__)) #the folder containing this script
os.chdir(localfolder)
remoteinvoicefolder = "O:\OSC\PaymentsAndCommitments\Waiver requests"
internfolder = os.path.join(home, ".OATs", "OutLAW")

warning_counter = 0

if not os.path.exists(internfolder):
    os.makedirs(internfolder)
    print('Please add files library_letter_paper.pdf and waiver_signature.png to folder', internfolder)

invoicefolder = localfolder
invoicevarfile = os.path.join(internfolder, "waiver-variables.txt")
if not os.path.exists(invoicevarfile):
    with open(invoicevarfile, "w") as f:
        f.write("OVERWRITE THIS WITH INVOICE INFO COPIED AND PASTED FROM ZENDESK")
overlayfile = os.path.join(invoicefolder, "OutLAW_overlay.tex")
filingfolder = remoteinvoicefolder

#SUMMON invoicevarfile AND overlayfile, THEN PROMPTS USER TO STAMP INVOICE
os.system("start " + invoicevarfile)
os.system("start " + overlayfile)

print("OutLAW: Please copy waiver data to", invoicevarfile, "if you have not done so already")
print("OutLAW: Please generate the waiver using TeXworks. You will need to typeset (click the green 'play' button) this document twice to correctly render the library's letterhead \n")
print("OutLAW: Rememeber you can uncomment lines 14-15 of", overlayfile, "to set variables manually\n")
a = input("After generating the waiver, please close the preview TeXworks window.\nHave you finished generating the waiver? (y/n)")
while a not in ["y", "Y", "yes", "YES"]:
    if a == "q":
        raise
    a = input("Have you finished generating the waiver? (y/n) (or q to quit)")

#OBTAIN INVOICE DATA AND RENAME THE FILE TO <OA/ZD NUMBER>_<INVOICE NUMBER>.PDF
print("OutLAW: Renaming waiver to <ZD NUMBER>_waiver.pdf")
input = open(invoicevarfile, 'r')
varcontent = input.read()
refno = ""
tzd = re.compile("ZD-[0-9]+")
mzd = tzd.search(varcontent)
if mzd:
    refno = mzd.group()
else:
    refno = "REF-ERROR"
    print("OutLAW ERROR: Failed to extract ZD number from", invoicevarfile)
    raise

invfilename = refno + "_waiver.pdf"    
src = os.path.join(invoicefolder, 'OutLAW_overlay.pdf')
dst = os.path.join(invoicefolder, invfilename)
OutLAW_copy(src, dst)

#FILE IT ON THE O: DRIVE
if invfilename not in os.listdir(filingfolder):
    src = os.path.join(invoicefolder, invfilename)
    dst = os.path.join(filingfolder, invfilename)
    OutLAW_copy(src, dst)
    print("OutLAW: moved waiver support letter to", filingfolder)
else:
    print("OutLAW ERROR: waiver already exists in", filingfolder)
    raise

#GET RID OF THE REMAINING TEMPORARY FILES
os.system("del OutLAW_overlay.aux OutLAW_overlay.log OutLAW_overlay.synctex.gz") #Windows version