# OATs

OATs (Open Access Tools) is a collection of scripts to automate some of the tasks performed by the Open Access Team at the Office of Scholarly Communication, University of Cambridge. Documentation on how to install and use these tools is provided below.

## Dependencies

Scripts in the OATs package rely on external tools for most of their functionality, so the following software will need to be installed in your machine in order for OATs to work:

* [Python 3](https://www.python.org)
* [TeX Live](https://www.tug.org/texlive) or another LaTeX installation containing the TikZ package
* [PDFtk](https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit) (a portable version of PDFtk for Windows is included in OATs, so Windows users can ignore this dependency)

## Installation

Simply clone or download this Github repository (C:\Users\<<your CRSid>>\OATs is the recommended installation path for OSC users).
  
## Configuration and usage

### OASIS (Open Access Service Invoice Stamper)

OASIS is an utility to digitally stamp and file PDFs of invoices sent to the OA helpdesk. To run OASIS on Windows, you may either:

* Double-click on file `C:\Users\<<your CRSid>>\OATs\OASIS\OASIS.cmd`
* Issue the following command on Command prompt: `%USERPROFILE%\AppData\Local\Programs\Python\Python36-32\python.exe %USERPROFILE%\OATs\oasis.py`

Or, on UNIX:

```
$ cd <path to OATS folder>
$ ./oasis.py
```

The first time it runs, the program will create a configuration file `~/.OATs/OASIS/config.txt` and ask you to edit this file to provide the full paths of:

* your browser download folder (i.e. the folder where the OASIS will be able to find invoices you have just downloaded)
* path to the shared OSC drive (this path can be different from the default if you are using the library's VPN, etc; please check). If, for any reason, you need to reconfigure OASIS to save invoices somewhere else, you may edit `C:\Users\<<your CRSid>>\.OATs\OASIS\config.txt` using your favorite plain text editor (e.g. Notepad++).
