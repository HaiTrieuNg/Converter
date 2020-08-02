# ----------------------------------------------------------------------
# Name: Converter
# Purpose:  Correcting and restoring the information
# that lost after using Pandoc to convert from Word to rst
#
# Author:   Trieu Nguyen
# ----------------------------------------------------------------------
"""
-Detecting and creating admonitions
-Detecting and creating codeblock
-Restore indents in codeblock using Artistic Style
-Allowing table without title row
-Delete the table of content that was originally in Word
-Fixing broken characters caused by double conversion
"""

import os
import sys
import re
import fileinput
import subprocess

print ("Please enter a file path with format: path\ filename.rst")

file= input( ">>" )

#list of admonitions
admonitions = ["attention", "caution", "danger", "error", "hint", "tip",
               "important", "note", "warning", "admonition"]

replacing_dict = {
    'â€“': "—",
    "â€”": "–",
    "â€˜": "‘",
    "â€™": "’",
    "Ã¢â‚¬â„¢": "’",
    "â€œ": "“",
    "â€": "”",
    "â€¢": "-",
    "â€¦": "…",
    "ï¼š": ":",
    "Ã˜": "Ø",
    "ÃƒËœ": "Ø"
}

count = 0
addIndent = False #if true, add indent to line for admonition content
dontAdd = False #don't add the line to result rst file
detected = False #a code block detected
tocDetected = False
tableDetected = False
emptyLine = False
noTitle  = False

try:

    with open(file, 'r+', encoding='UTF-8') as input_file:

        #define html element for adding newline
        input_file.write (".. |br| raw:: html\n\n"+"     <br/>\n\n")

        #go through each line of the rst file
        for line in fileinput.FileInput(file):

            #list of words in the line
            words = line.split()

             # take care of broken character caused by double conversion
            if line.split() or (len(words) == 1 \
                and words[0].strip() != "#") :
                for key in replacing_dict:
                    if key in line:
                        line = line.replace(key, replacing_dict[key])


            #done writing code block (with no indent) to a text file
            #continue the next steps with AStyle
            # and wrting back from text file to rst file
            if detected is True \
                    and (len(words) == 1 and words[0].strip() == "#"):
                detected = False
                codeFile.close()

                #Calling AStyle to add indent to the text file content

                command = "astyle --style=allman " + textFile
                process = subprocess.Popen(command,
                                           stdout=subprocess.PIPE)
                output, error = process.communicate()

                #Reopenning text file and
                # write the text content back to the result rst
                try:
                    with open(textFile, 'r+',
                              encoding='UTF-8') as codeblock_file:
                        for codeLine in codeblock_file:
                            # check an replace error characters in code
                            for key in replacing_dict:
                                if key in codeLine:
                                    codeLine = codeLine.replace \
                                        (key, replacing_dict[key])
                            #add code line from txt file to new rst file

                            input_file.write("    " + codeLine)

                        input_file.write("\n")

                        codeblock_file.close()

                except FileNotFoundError as error:
                    # if the file can't be found
                    print(error)

            #write codeblock line from rst to a text file
            elif detected is True  and \
                    (len(words) != 0 and words[0].strip() != "#"):
                codeFile.write(line)


            #table without title, replaceing "=" with "-"
            if noTitle is True and tableDetected is True:
                line = line.replace("=", "-")
                noTitle = False
                tableDetected = False

            #table without title found (no bold characters in first row)
            elif tableDetected is True and "**" not in line:
                noTitle = True

            # toc detected,
            # not adding next lines that start with numbers to final rst
            # until a line start with letters (end of toc)
            elif tocDetected and line.split() \
                    and not words[0].strip().replace('.', "1").isdigit():
                tocDetected = False

            #end of codeblock in rst, start adding lines normally again
            elif dontAdd is True and len(words) == 1 \
                and words[0].strip() == "#" :
                line = "\n"
                dontAdd = False

            #use # to mark the need of a newline
            #since pandoc deletes all newlines when converting
            elif len(words) == 1 and words[0].strip() == "#":
                line = "\n"
                addIndent = False

            #add indents,rst now reads the line as admonitions's content
            #since pandoc takes away indents when converting
            elif addIndent is True and line.split() \
                    and words[0].strip() != "#":
                line = "     " + line.strip() + " |br|\n"


            #Spot an admonition
            elif len(words) == 1 and words[0].replace("**","").isalpha() \
                    and words[0].lower().replace("**","") in admonitions:
                addIndent = True #set addIndent to true
                line = ".. " + words[0].lower().replace("**","") + "::\n"

            #Spot code block and language
            elif len(words) == 2 and \
                    words[0].lower().replace("**","") == "code-block":

                #while true, don't add Pandoc rst content to final rst
                dontAdd = True
                #while true, we are still in the code blok cotent
                detected = True

                #alter and add the title "code-block language" first
                line = ".. " + words[0].lower().replace("**","") + ":: "\
                            + words[1].replace("**","")+ "\n\n"

                input_file.write(line)

                #new text file name
                #code block from rst will be added to this text file
                count = count + 1;
                textFile = str(count) + ".txt"

                #creating the new text file with the above name
                codeFile = open(textFile, "a+")

            elif line.lower().replace("**","").strip() == "table of contents":
                tocDetected = True

            elif emptyLine is True and line.count("+") >= 2 and\
                    line.count("-") >= 2 :
                tableDetected = True
                emptyLine = False
            #delete the extra empty lines caused by
            # converting from Word to rst

            elif not line.split() or (len(words) == 1 and
                words[0] == "|br|"):
                emptyLine = True


            if tocDetected or (dontAdd is True or
                addIndent is True and len(words) == 1 and
                words[0] == "|br|") or \
                (addIndent is True and not line.strip()):
                pass
            else:
            #add the lines to the file
                input_file.write(line)

    input_file.close()
    print ("The task is completed.")

except FileNotFoundError as error:
    # if the file can't be found
    print(error)



