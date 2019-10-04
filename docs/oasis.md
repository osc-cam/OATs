## OASIS (Open Access Service Invoice Stamper)

OASIS is OATs' flagship utility. It can be used to digitally stamp and file PDFs of invoices sent to the OA helpdesk. To run OASIS on Windows, 

* Open the Windows program "Command prompt"
* Issue the following command on the Command prompt window: `C:\Applications\<WinPython folder>\<python version folder>\python.exe %USERPROFILE%\OATs-master\oasis.py`, replacing <WinPython folder>\<python version folder> for the correct path in your machine. See the [troubleshooting](#specifying-the-correct-path) section below for more details if you encounter problems here. TIP: To paste from your clipboard into the command prompt window, right-click on it and select "paste". 

If you are a UNIX user (Linux, Mac OS), issue these commands in your terminal:

```
$ cd <path to OATS folder>
$ ./oasis.py
```

The first time it runs, the program will create a configuration file `~/.OATs/OASIS/config.txt` and ask you to edit this file to provide the full paths of:

* your browser download folder (i.e. the folder where OASIS will be able to find invoices you have just downloaded)
* path to the shared OSC drive (this path can be different from the default if you are using the library's VPN, etc; please check). If, for any reason, you need to reconfigure OASIS to save invoices somewhere else, you may edit `C:\Users\<<your CRSid>>\.OATs\OASIS\config.txt` using your favorite plain text editor (e.g. Notepad++).

### Usage

* Download the invoice (if your browser is not configured to automatically save PDF files, you will need to save the invoice file to the folder you configured above)
* Navigate to the relevant ticket in Zendesk (the one with a decision on the manuscript)
* Fill in the relevant details in Zendesk (funding codes, invoice number, invoice date, etc)
* Apply Zendesk macro "Export invoice data (OASIS)" (but do not save the ticket)
* Summon OASIS by:
    * If this is the first invoice you are processing today:
        * Copying the line of the Zendesk macro output that is tagged with %%YOUR NAME
        * Opening program "Command prompt"
        * Pasting and hiting "Enter/Return" (the shortcut Ctrl+V does not work in the command prompt, so you will need to right click the prompt and select "paste")
        * Leave the command prompt window to facilitate processing subsequent invoices
    * If you have already processed an invoice today (and left command prompt running):
        *  Press the up arrow key (↑) on your keyboard, followed by "Enter/Return"  

* Follow the instructions on the screen, which will involve:
    * Selecting and copying all the text of the internal note that was produced in Zendesk (Ctrl+A, Ctrl+C)
    * Pasting that text into invoice-variables.txt and saving that file (Ctrl+V, Ctrl+S)
    * Using Texworks to stamp the invoice (please close TexWorks once you have done this)
    * Confirming that you are happy with the result (by typing "y" and pressing Enter on the command prompt window)

* Either delete the text produced in Zendesk by the OASIS macro or replace it with a reference to the ticket containing the original invoice.
    
OASIS will perform the following actions automatically:

* move the stamped invoice to the print folder on the shared drive \\OSC\PaymentsAndCommitments\Invoices\Invoices_to_print
* file a copy of the invoice in the archive folder on the shared drive \\OSC\PaymentsAndCommitments\Invoices\Invoices to be checked

Regularly send all invoices in the print folder to the printer and move then to "Printed_just_now" subfolder. Once you have confirmed that all invoices were printed correctly:
 * please delete the contents of the "Printed_just_now" subfolder
 * place the printed invoices in the bottom tray of the black 3-compartments organiser labelled "INVOICES for Danny"

### Tips

#### Moving the stamp

You can adjust the position of the electronic stamp produced by OASIS by changing the following two lines of the output produced by the OASIS Zendesk macro:

```
\newcommand{\xshift}{-7.5}
\newcommand{\yshift}{-4}
``` 

xshift and yshift control, respectively, the horizontal and vertical position of the stamp. The numeric value is in centimetres. Thus, to move the stamp down by 2 centimetres you would need to change the value of yshift from -4 to -6, as shown below:

```
\newcommand{\xshift}{-7.5}
\newcommand{\yshift}{-6}
```

The valid ranges of values for these two parameters are:

* xshift: -10 (left margin) to -5 (right margin)  
* yshift: -15.5 (bottom of page) to 12.5 (top of page)

### Troubleshooting

#### Specifying the correct path

If when attempting to run OASIS you encounter error message "The system cannot find the path specified", this means that python 3 is not installed in the location (the "path") we expected it to be (i.e. "C:\Applications\Wpy [...] \python.exe"). To fix this, search for the installed python application (file python.exe) through Windows Explorer (clicking "Local disk C:", then "Applications"; then "WinPython" folder. When this is done, click on the search bar at the top of Windows Explorer and copy paste the line that appears. Add “\python.exe” at the end and this gives you the "path" to that file. Send this full path to one of your coleagues who is responsible for updating Zendesk Macros.

Your colleague should then update the [OASIS Zendesk macro](../pdfapps/oasis/zd-macro.txt) to include, near the end of the file, your personal path, written as follows leave the % signs as they are):

```
%% YOUR FIRST NAME
% [copy/paste the python path here without brackets] %USERPROFILE%\OATS\oasis.py
```
