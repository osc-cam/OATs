# OATs

OATs (Open Access Tools) is a collection of software to automate some of the tasks performed by the Open Access Team at the Office of Scholarly Communication (OSC), University of Cambridge. Documentation for OSC staff on how to install and use these tools is provided below.

## Dependencies

Software in the OATs package rely on external tools for most of their functionality, so the following software will need to be installed in your machine in order for OATs to work:

### [Python 3](https://www.python.org)

You have (at least) two choices to solve this dependency:

* (recommended) install the latest version of [WinPython](https://sourceforge.net/projects/winpython), which is a portable python distribution. You can install it wherever you like. If you don't have a preference, a sensible place would be: C:\Applications\WinPython\ (you can easily create an "Applications" folder using Windows Explorer if needed).
* download and run the Windows installer of the official Python release. This option is only recommended for users that have administrative rights to their machines (not the case for Windows desktops available to OSC members). 


### [TeX Live](https://www.tug.org/texlive) 

TeX Live provides a comprehensive LaTeX system with all packages you will need to run OATs utilities. Alternatively, you can solve this dependency by using another LaTeX installation containing the TikZ package. To install TeX Live, download and run the [Windows installer](http://mirror.ctan.org/systems/texlive/tlnet/install-tl-windows.exe).

If you run into error "perl.exe has stopped working", try selecting "Custom install" instead of "Simple install (big)".

#### Associating the extension .tex to TeXworks

Once the TeX Live installation has finished, please associate the extension .tex to the new program TeXworks. To do this:

* Using Windows Explorer, navigate to any .tex file on your computer (O:\OSC\Open Access\OATs contains file Dummy_tex_document.tex for your convenience)
* Right-click on the .tex file and choose "Properties"
* Locate the option "Opens with" and click "Change...", then "Browse..."
* Find and select the TeXworks executable (C:\texlive\2016\bin\win32\texworks.exe)


### A good plain text editor 

UNIX users can probably use whichever text editor they prefer (I can confirm it works fine with [gedit](https://wiki.gnome.org/Apps/Gedit))

Windows users should install Notepad++, which is available as a portable application [here](https://portableapps.com/apps/development/notepadpp_portable), and then associated the .txt file extension to this program, as explained below.

#### Associating the extension .txt to Notepad++

To do this:

* Using Windows Explorer, navigate to any .txt file on your computer
* Right-click on the .txt file and choose "Properties"
* Locate the option "Opens with" and click "Change...", then "Browse..."
* Find and select the Notepad++ executable


### [PDFtk](https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit)

A portable version of PDFtk for Windows is included in OATs, so Windows users can ignore this dependency.

#### PDFtk on Ubuntu 18.04

PDFtk is not available from the official Ubuntu 18.04 repositories. See https://askubuntu.com/a/1028983 for installation instructions.

## OATs Installation

Simply clone or download this Github repository (C:\Users\\<\<your CRSid>>\OATs-master is the recommended installation path i.e. the extracted files should be in this directory).
  
## Configuration and usage

Please click the links below for configuration and usage instructions for each of OATs' utilities:

* [OASIS (Open Access Service Invoice Stamper)](./docs/oasis.md)
* [OutLAW (Outputs Letter of support for Apc Waiver application)](./docs/outlaw.md)
