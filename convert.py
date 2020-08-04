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
-Applying title row to table that missing title row
-Delete the table of content that was originally in Word
-Fixing broken characters caused by double conversion
"""

import os
import sys
import re
import fileinput
import subprocess

print("Please enter a file path with format: path\ filename.rst")

file = input(">>")

# list of admonitions
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

count = 0 # for codeblock text file name
addIndent = False  # if true, add indent to line for admonition content
dontAdd = False  # don't add the line to result rst file
detected = False  # a code block detected
tocDetected = False
tableDetected = False
noTitle = False
prevLine = ""
haveTitle = False
emptyTitle = False
sTableDetected = False


try:

    with open(file, 'r+', encoding='UTF-8') as input_file:

        # go through each line of the rst file
        lines = input_file.readlines()
        input_file.seek(0, 0)

        # define html element for adding newline
        input_file.write(".. |br| raw:: html\n\n" + "     <br/>\n\n")

        # go through each line of the rst file
        # for line in fileinput.FileInput(file):

        for line in lines:

            # list of words in the line
            words = line.split()
            # print("Words=", words)

            if emptyTitle is True :
                if line.strip().replace("=", "1").replace("-", "1").\
                        replace("~", "1").isdigit():
                    line = ""
                emptyTitle = False

            if tocDetected is True and line.split() and \
                    (line.strip().replace("=", "1").replace("-", "1").
                             replace("~", "1").isdigit()
                     and prevLine.lower().replace("**", "").
                             strip() != "table of contents"):
                input_file.write(prevLine)
                tocDetected = False
            elif line.lower().replace("**", "").strip() == "table of contents":
                tocDetected = True

            # take care of broken character caused by double conversion
            if line.split() or (len(words) == 1 \
                                and words[0].strip() != "#"):
                for key in replacing_dict:
                    if key in line:
                        line = line.replace(key, replacing_dict[key])

            # done writing code block (with no indent) to a text file
            # continue the next steps with AStyle
            # and wrting back from text file to rst file
            if detected is True \
                    and (len(words) == 1 and
                         words[0].strip().replace("**", "") == "#"):
                detected = False
                codeFile.close()

                # Calling AStyle to add indent to the text file content

                command = "astyle --style=allman " + textFile
                process = subprocess.Popen(command,
                                           stdout=subprocess.PIPE)
                output, error = process.communicate()

                # Reopenning text file and
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
                            # add code line from txt file to new rst file

                            input_file.write("    " + codeLine)

                        input_file.write("\n")

                        codeblock_file.close()

                except FileNotFoundError as error:
                    # if the file can't be found
                    print(error)

            # write codeblock line from rst to a text file
            elif detected is True and \
                    (len(words) != 0 and
                     words[0].strip().replace("**", "") != "#"):
                codeFile.write(line)

            # table without title, replaceing "=" with "-"
            if noTitle is True and tableDetected is True:
                line = line.replace("=", "-")
                noTitle = False
                tableDetected = False
            elif haveTitle is True and tableDetected is True:
                line = line.replace("-", "=")
                haveTitle = False
                tableDetected = False
            # table without title found (no bold characters in first row)
            elif tableDetected is True and "**" not in line:
                noTitle = True
            elif tableDetected is True and line.count("**") >= 4:
                haveTitle = True



                # toc detected,
            # not adding next lines that start with numbers to final rst
            # until a line start with letters (end of toc)


            # end of codeblock in rst, start adding lines normally again
            if dontAdd is True and len(words) == 1 \
                    and words[0].strip().replace("**", "") == "#":

                emptyTitle = True
                line = "\n"
                dontAdd = False

            # use # to mark the need of a newline
            # since pandoc deletes all newlines when converting
            elif len(words) == 1 and \
                    words[0].strip().replace("**", "") == "#":
                line = "\n"
                addIndent = False
                emptyTitle = True

            # add indents,rst now reads the line as admonitions's content
            # since pandoc takes away indents when converting
            elif addIndent is True and line.split() \
                    and words[0].strip().replace("**", "") != "#":
                if line.strip()[-1] == "*":
                    line = "     " + line.strip() + " |br|\n"
                else:
                    line = "     " + line.strip()

            # Spot an admonition
            elif (len(words) == 1 and words[0].replace("**", "").isalpha() \
                    and words[0].lower().replace("**", "").strip()
                  in admonitions)\
                    or (len(words) == 2 and words[1].lower().replace("**", "")
                    .strip() in admonitions):
                addIndent = True  # set addIndent to true
                if len(words) == 1:
                    line = ".. " + words[0].lower().replace("**", "") + "::\n"
                else:
                    line = ".. " + words[1].lower().replace("**", "") + "::\n"

            # Spot code block and language
            elif (len(words) == 2 and \
                    words[0].lower().replace("**", "")
                            .strip() == "code-block")\
                    or (len(words) == 3 and
                        words[1].lower().replace("**", "")
                                .strip() == "code-block"):

                # while true, don't add Pandoc rst content to final rst
                dontAdd = True
                # while true, we are still in the code blok cotent
                detected = True

                # alter and add the title "code-block language" first
                if len(words) == 2:
                    line = ".. " + words[0].lower().replace("**", "") + ":: " \
                       + words[1].replace("**", "") + "\n\n"
                else:
                    line = ".. " + words[1].lower().replace("**", "") + ":: " \
                           + words[1].replace("**", "") + "\n\n"

                input_file.write(line)


                # new text file name
                # code block from rst will be added to this text file
                count = count + 1;
                textFile = str(count) + ".txt"

                # creating the new text file with the above name
                codeFile = open(textFile, "a+")







            elif  (not prevLine.split() or (len(prevLine) == 1
                                            and prevLine[0] == "|br|"))\
                    and line.count("+") >= 2 and \
                    line.count("-") >= 2 and line.count("-+-") >= 1:
                tableDetected = True
                #emptyLine = False

            # delete the extra empty lines caused by
            # converting from Word to rst
            #elif not line.split() or (len(words) == 1 and
            #                          words[0] == "|br|"):
            #    emptyLine = True



            if line.strip().replace("=","1").replace(" ", "2").isdigit()\
                    and  (not prevLine.split() or (len(prevLine) == 1 and prevLine[0] == "|br|")) \
                    and tocDetected is False and tableDetected is False:
                sTableDetected = True
            elif sTableDetected is True and line.count("**")>=4:
                line = line + prevLine
                print( line)
                sTableDetected = False
            elif sTableDetected is True and line.count("**")<=4:
                sTableDetected = False

            #if tocDetected is True:
                #help with marking the end of TOC
            prevLine = line

            if tocDetected is True or (dontAdd is True or
                               addIndent is True and len(words) == 1 and
                               words[0] == "|br|") or \
                    (addIndent is True and not line.strip()):
                pass
            else:
                # add the lines to the file
                input_file.write(line)



        #delete the remaining mapping lines
        input_file.truncate(input_file.tell())

    input_file.close()
    print("The task is completed.")

except FileNotFoundError as error:
    # if the file can't be found
    print(error)



