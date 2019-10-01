### OutLAW (Output Letter of support for Apc Waiver application)

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
