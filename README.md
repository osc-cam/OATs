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

Please click the links below for configuration and usage instructions for each of OATs' utilities:

* [OASIS (Open Access Service Invoice Stamper)](./docs/oasis.md)
* [OutLAW (Outputs Letter of support for Apc Waiver application)](./docs/outlaw.md)
