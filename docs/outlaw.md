### OutLAW (Output Letter of support for Apc Waiver application)

OutLAW is an utility to produce letters of support for APC waiver applications. To run OutLAW on Windows:

* Open the Windows program "Command prompt"
* Issue the following command on the Command prompt window: `C:\Applications\<WinPython folder>\<python version folder>\python.exe %USERPROFILE%\OATs-master\outlaw.py`, replacing <WinPython folder>\<python version folder> with the correct path in your machine. See the [troubleshooting](./oasis.md#specifying-the-correct-path) section of OASIS' documentation for more details if you encounter problems here. TIP: To paste from your clipboard into the command prompt window, right-click on it and select "paste".

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

[This short video](https://sms.cam.ac.uk/media/3081863) demonstrates OutLAW typical usage. The steps to follow in a Windows machine are:

* Navigate to the relevant ticket in Zendesk (usually this is the SE- submission ticket)
* Apply Zendesk macro "Export waiver data (OutLAW)" (but do not save the ticket)
* Summon OutLAW:
    * From the Zendesk macro output, copy the line that is just below the tag %%YOUR NAME (this is your python path; see [troubleshooting](./oasis.md#specifying-the-correct-path) for details)
    * Open the program "Command prompt"
    * Paste and hit "Enter/Return" (the shortcut Ctrl+V does not work in the command prompt, so you will need to right click the prompt and select "paste")
* Follow the instructions on the command prompt window, which will involve:
    * Selecting and copying all the text of the internal note that was produced in Zendesk (Ctrl+A, Ctrl+C)
    * Pasting that text into waiver-variables.txt and saving that file (Ctrl+V, Ctrl+S)
    * Using Texworks to generate the waiver letter (you will need to typeset [click the green "play" button] it twice to correctly render the library's letterhead)
    * Confirming that you are happy with the result

OutLAW will place the resulting letter (expected filename is ZD-#######_waiver.pdf, where ####### is the Zendesk ticket number) in folder C:\Users\<<your CRSid>>\OATs-master\pdfapps\outlaw
