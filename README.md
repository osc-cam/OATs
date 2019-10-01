# OATs

OATs (Open Access Tools) is a collection of scripts to automate some of the tasks performed by the Open Access Team at the Office of Scholarly Communication (OSC), University of Cambridge. Documentation for OSC staff on how to install and use these tools is provided below.

## Dependencies

Scripts in the OATs package rely on external tools for most of their functionality, so the following software will need to be installed in your machine in order for OATs to work:

### [Python 3](https://www.python.org)

You have (at least) two choices to solve this dependency:

* (recommended) install the latest stable version of WinPython, which is a portable python distribution. You can install it wherever you like. If you don't have a preference, a sensible place would be: C:\Applications\WinPython\
* download and run the Windows installer of the official Python release. As you do not have admin rights to your machine, you will need to untick the box "Install launcher for all users" before clicking "Install Now".

The first method is the recommended one because, if you are installing OATs in a second UL machine (i.e. you have installed it previously in a different UL computer using the official release), it is very likely that the second method will fail due to errors associated with your network user profile.

### [TeX Live](https://www.tug.org/texlive) 

TeX Live provides a comprehensive LaTeX system with all packages you will need to run OATs utilities. Alternatively, you can solve this dependency by using another LaTeX installation containing the TikZ package. To install TeX Live, download and run the [Windows installer](http://mirror.ctan.org/systems/texlive/tlnet/install-tl-windows.exe).

If you run into error "perl.exe has stopped working", try selecting "Custom install" instead of "Simple install (big)".

#### Associating the extension .tex to TeXworks

Once the TeX Live installation has finished, please associate the extension .tex to the new program TeXworks. To do this:

* Using Windows Explorer, navigate to any .tex file on your computer (O:\OSC\Open Access\OATs contains file Dummy_tex_document.tex for your convenience)
* Right-click on the .tex file and choose "Properties"
* Locate the option "Opens with" and click "Change...", then "Browse..."
* Find and select the TeXworks executable (C:\texlive\2016\bin\win32\texworks.exe)

### [PDFtk](https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit)

A portable version of PDFtk for Windows is included in OATs, so Windows users can ignore this dependency.

#### PDFtk on Ubuntu 18.04

PDFtk is not available from the official Ubuntu 18.04 repositories. See https://askubuntu.com/a/1028983 for installation instructions.

## OATs Installation

Simply clone or download this Github repository (C:\Users\\<\<your CRSid>>\OATs is the recommended installation path).
  
## Configuration and usage

### OASIS (Open Access Service Invoice Stamper)

OASIS is OATs' flagship utility. It can be used to digitally stamp and file PDFs of invoices sent to the OA helpdesk. To run OASIS on Windows, you may either:

* Double-click on file `C:\Users\<<your CRSid>>\OATs\oasis.cmd`
* Issue the following command on Command prompt: `%USERPROFILE%\AppData\Local\Programs\Python\Python36-32\python.exe %USERPROFILE%\OATs\oasis.py`

Or, on UNIX:

```
$ cd <path to OATS folder>
$ ./oasis.py
```

The first time it runs, the program will create a configuration file `~/.OATs/OASIS/config.txt` and ask you to edit this file to provide the full paths of:

* your browser download folder (i.e. the folder where OASIS will be able to find invoices you have just downloaded)
* path to the shared OSC drive (this path can be different from the default if you are using the library's VPN, etc; please check). If, for any reason, you need to reconfigure OASIS to save invoices somewhere else, you may edit `C:\Users\<<your CRSid>>\.OATs\OASIS\config.txt` using your favorite plain text editor (e.g. Notepad++).

#### Usage

Download the invoice
Navigate to the relevant ticket in Zendesk (the one with a decision on the manuscript)
Fill in the relevant details in Zendesk (funding codes, invoice number, invoice date, etc)
Apply Zendesk macro "Export invoice data (OASIS)"
Summon OASIS by either:
Double-clicking on file C:\Users\<<your CRSid>>\OATs\OASIS\OASIS.cmd and reassuring Windows that you know what you are doing.
Or (although this method requires more steps, it is useful for processing several invoices in one go):
Copying the last line of the Zendesk macro output
Opening program "Command prompt"
Pasting and hiting "Enter/Return"
If at this point you encounter error message "The system cannot find the path specified", this means that python 3 is not installed in the location we expected it to be (%USERPROFILE%\AppData\Local\Programs\Python\Python36-32\python.exe). To fix this, search for python.exe using Windows Explorer and then adjust the last line of the Zendesk macro output accordingly. It will most likely be in a similar path if you installed a different version of python 3 using the default settings (the last subfolder of the path indicates the python version).

Follow the instructions on the screen, which will involve:
Configuring the script (setting your downloads and print) if this is the first time you run it (see section Configuration for more details)
Selecting and copying all the text of the internal note that was produced in Zendesk (Ctrl+A, Ctrl+C)
Pasting that text into invoice-variables.txt and saving that file (Ctrl+V, Ctrl+S)
Using Texworks to stamp the invoice
Confirming that you are happy with the result
OASIS should then perform the following actions automatically:

move the stamped invoice to the print folder on the shared drive \\OSC\PaymentsAndCommitments\Invoices\Invoices_to_print
file a copy of the invoice in the archive folder on the shared drive \\OSC\PaymentsAndCommitments\Invoices\Invoices to be checked
Regularly send all invoices in the print folder to the printer and move then to "Printed_just_now" subfolder. Once you have confirmed that all invoices were printed correctly, please delete the contents of the "Printed_just_now" subfolder.

### OutLAW (Output LaTeX APC Waiver)

OutLAW is an utility to produce letters of support for APC waiver applications. To run OutLAW on Windows, you may either:

* Double-click on file `C:\Users\<<your CRSid>>\OATs\outlaw.cmd`
* Issue the following command on Command prompt: `%USERPROFILE%\AppData\Local\Programs\Python\Python36-32\python.exe %USERPROFILE%\OATs\outlaw.py`

Or, on UNIX:

```
$ cd <path to OATS folder>
$ ./oulaw.py
```

To produce the a support letter, OutLAW requires:

* a PDF copy of the letterhead to be used (a copy of UL's letterhead is available in the OSC shared drive at \\OSC\Open Access\OATs\library-letter-paper.pdf)
* a bitmap containing the signature of the person producing the letter (i.e. your signature). This should be roughly 200 pixels wide by 150 pixels high and you can create it by using graphics tablets or by scanning a piece of paper with your signature and then cropping the resulting image

Please place these documents in your local OutLAW's configuration folder C:\Users\<<your CRSid>>\.OATs\OutLAW (you may need to create subfolders .OATS and OutLAW).

#### Usage

* Navigate to the relevant ticket in Zendesk (the one with a decision on the manuscript)
* Apply Zendesk macro "Export waiver data (OutLAW)"
* Summon OutLAW by either:
..* Double-clicking on file C:\Users\<<your CRSid>>\OATs\OutLAW\OutLAW.cmd and reassuring Windows that you know what you are doing.
..* Or:
....* Copying the last line of the Zendesk macro output
....* Opening program "Command prompt"
....* Pasting and hiting "Enter/Return"
* Follow the instructions on the screen, which will involve:
..* Selecting and copying all the text of the internal note that was produced in Zendesk (Ctrl+A, Ctrl+C)
..* Pasting that text into waiver-variables.txt and saving that file (Ctrl+V, Ctrl+S)
..* Using Texworks to generate the waiver letter (you will need to typeset (click the green 'play' button) it twice to correctly render the library's letterhead)
..* Confirming that you are happy with the result

OutLAW will place the resulting letter in folder C:\Users\<<your CRSid>>\OATs\OutLAW
