#!/usr/bin/env python3

import os
import sys
import re
import subprocess
import time

from pdfapps.helpers import oats_copy


def setup_os(platform_string=sys.platform, home=os.path.expanduser("~")):
    username = home.split('/')[-1]
    rm_cmd = 'rm'
    texworks = 'texworks'
    if platform_string.startswith('linux'):
        open_cmd = 'xdg-open'
    elif platform_string.startswith('win32'):
        open_cmd = 'start'
        rm_cmd = 'del'
        username = home.split("\\")[-1]
    elif platform_string.startswith('darwin'):  # MAC OS
        open_cmd = 'open'
    else:
        print('OutLAW ERROR: Operational system', platform_string,
                    'not supported. OutLAW will attempt to apply linux parameters')
        open_cmd, rm_cmd, username, home, texworks = setup_os('linux')
    return (open_cmd, rm_cmd, username, home, texworks)


print(
    '''OutLAW 0.5

Author: André Sartori
Copyright (c) 2017

OutLAW is part of OATs. The source code and documentation can be found at
https://github.com/osc-cam/OATs

You are free to distribute this software under the terms of the GNU General Public License.  
The complete text of the GNU General Public License can be found at 
http://www.gnu.org/copyleft/gpl.html

'''
)

# SET UP PROGRAM VARIABLES
outlawfolder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pdfapps', 'outlaw')  # the folder containing this script
os.chdir(outlawfolder)
open_cmd, rm_cmd, username, home, texworks = setup_os()

# CHECK THAT TEXWORKS CAN BE FOUND; IF NOT USE DEFAULT OS APPLICATION INSTEAD
try:
    subprocess.run([texworks, '-v'], stdout=open(os.devnull, 'w'), check=True)
except FileNotFoundError:
    texworks = open_cmd

auxiliary_folder = os.path.join(home, ".OATs", "OutLAW")

warning_counter = 0

if not os.path.exists(auxiliary_folder):
    os.makedirs(auxiliary_folder)
    print('Please add files library_letter_paper.pdf and waiver_signature.png to folder', auxiliary_folder)

waiver_var_file = os.path.join(auxiliary_folder, "waiver-variables.txt")
if not os.path.exists(waiver_var_file):
    with open(waiver_var_file, "w") as f:
        f.write("OVERWRITE THIS WITH WAIVER INFO COPIED AND PASTED FROM ZENDESK")
overlayfile = os.path.join(outlawfolder, "OutLAW_overlay.tex")

# SUMMON waiver_var_file AND overlayfile, THEN PROMPTS USER TO STAMP INVOICE
os.system(open_cmd + ' ' + waiver_var_file)
time.sleep(0.5)
os.system(texworks + ' ' + overlayfile)

print("OutLAW: Please copy waiver data to", waiver_var_file, "if you have not done so already")
print("OutLAW: Please generate the waiver using TeXworks. You will need to typeset (click the green 'play' button) this document twice to correctly render the library's letterhead \n")
print("OutLAW: Rememeber you can uncomment lines 14-15 of", overlayfile, "to set variables manually\n")
a = input(
    "After generating the waiver, please close the preview TeXworks window.\nHave you finished generating the waiver? (y/n)")
while a not in ["y", "Y", "yes", "YES"]:
    if a == "q":
        sys.exit()
    a = input("Have you finished generating the waiver? (y/n) (or q to quit)")

# OBTAIN WAIVER DATA AND RENAME THE FILE TO <OA/ZD NUMBER>_waiver.pdf
print("OutLAW: Renaming waiver to <ZD NUMBER>_waiver.pdf")
input = open(waiver_var_file, 'r')
varcontent = input.read()
refno = ""
tzd = re.compile("ZD-[0-9]+")
mzd = tzd.search(varcontent)
if mzd:
    refno = mzd.group()
else:
    sys.exit("OutLAW ERROR: Failed to extract ZD number from " + waiver_var_file)

waiver_filename = refno + "_waiver.pdf"
src = os.path.join(outlawfolder, 'OutLAW_overlay.pdf')
dst = os.path.join(outlawfolder, waiver_filename)
oats_copy(src, dst)

# GET RID OF THE REMAINING TEMPORARY FILES
os.system(rm_cmd + " OutLAW_overlay.aux OutLAW_overlay.log OutLAW_overlay.synctex.gz")