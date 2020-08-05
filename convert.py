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


def isEmptyLine (line):
    """
    Check if a line is empty
    :param: the line to be checked
    :return: boolean- True if the line is empty
    """
    return not line.split() or (len(line) == 1 and line[0] == "|br|")


def isNumberSign (word):
    """
    Check if a word is "#"
    :param: the word to be checked
    :return: boolean- True if the the word is "#"
    """
    return word.strip().replace("**", "") == "#"


def isAdmonition (title):
    """
    Check if the line is the title of an admonition
    :param: the line to be checked
    :return: boolean- True if the line is the title of an admonition
    """
    # list of admonitions
    admonitions = ["attention", "caution", "danger", "error", "hint", "tip",
                   "important", "note", "warning", "admonition"]

    return title.lower().replace("**", "").strip() in admonitions


def rstAdmonition (title):
    """
    Replacing the line with rst formatted admonition title
    :param title: the title line
    :return: string - title string with the correct rst format
    """
    return ".. " + title.lower().replace("**", "") + "::\n"


def isCodeblock (word):
    """
    Check if this is a start of code block
    :param word: the word to be checked
    :return: boolean- if this is the start of codeblock
    """
    return word.lower().replace("**", "").strip() == "code-block"


def codeblockTitle (title, language):
    """
    Replacing the line with rst formatted codeblock title
    :param title: string- code-block
    :param language: string- the language
    :return: string - codeblock title string with the correct rst format
    """
    return ".. " + title.lower().replace("**", "") + ":: " \
                           + language.replace("**", "") + "\n\n"


def content (line):
    """
    Format the content of admonition
    :param line: the line to be changed
    :return: string- formatted line
    """
    return "     " + line.strip()


def lineOfSymbol (line):
    """
    Check if a line is just full of symbol, no text
    :param line: the line to be checked
    :return: boolean- True if the line just have symbols, no text
    """
    return line.strip().replace("=", "1").replace("-", "1").\
                            replace("~", "1").isdigit()


def isTOCtitle (line):
    """
    Check if the line is the TOC title
    :param line: the line to be checked
    :return: boolean- True if the line is a TOC title
    """
    return line.lower().replace("**", "").strip() == "table of contents"


def error_check (line):

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

    for key in replacing_dict:
        if key in line:
            return line.replace(key, replacing_dict[key])
        else:
            return line

def main():

    print("Please enter a file path with format: path\ filename.rst")

    file = input(">>")

    count = 0 # for codeblock text file name
    addIndent = False  # if true, add indent to line for admonition content
    dontAdd = False  # don't add the line to result rst file
    detected = False  # a code block detected
    tocDetected = False #detect a toc to delete
    tableDetected = False #detect grid table
    noTitle = False #grid table with no title detected
    prevLine = "" #keep track of previous line
    haveTitle = False #table should have title detected
    emptyTitle = False
    sTableDetected = False #simple table detected


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

                if emptyTitle :
                    if lineOfSymbol (line):
                        line = ""
                    emptyTitle = False

                #end of TOC, start writing again
                if tocDetected and line.split() and \
                        (lineOfSymbol (line)  and not isTOCtitle (prevLine)):
                    input_file.write(prevLine)
                    tocDetected = False
                #TOC detected
                elif isTOCtitle (line):
                    tocDetected = True

                # take care of broken character caused by double conversion
                if line.split() or (len(words)== 1 and isNumberSign(words[0])):
                        line = error_check (line)

                # done writing code block (with no indent) to a text file
                # continue the next steps with AStyle
                # and wrting back from text file to rst file
                if detected \
                        and (len(words) == 1 and isNumberSign(words[0])):
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
                                codeLine = error_check (codeLine)
                                # add code line from txt file to new rst file

                                input_file.write("    " + codeLine)

                            input_file.write("\n")

                            codeblock_file.close()

                    except FileNotFoundError as error:
                        # if the file can't be found
                        print(error)

                # write codeblock line from rst to a text file
                elif detected and \
                        (len(words) != 0 and not isNumberSign(words[0])):
                    codeFile.write(line)

                # table should not have a title, replaceing "=" with "-"
                if noTitle and tableDetected is True:
                    line = line.replace("=", "-")
                    noTitle = False
                    tableDetected = False
                #table should have a title
                elif haveTitle and tableDetected is True:
                    line = line.replace("-", "=")
                    haveTitle = False
                    tableDetected = False
                # table without title found (no bold characters in first row)
                elif tableDetected  and "**" not in line:
                    noTitle = True
                # table with title found
                # has more than 2 old characters in first row
                elif tableDetected  and line.count("**") >= 4:
                    haveTitle = True

                # end of codeblock in rst, start adding lines normally again
                if dontAdd  and len(words) == 1 and\
                        isNumberSign(words[0]):
                    emptyTitle = True
                    line = "\n"
                    dontAdd = False

                # use # to mark the need of a newline
                # at places that needed newlines were deleted by Pandoc
                elif len(words) == 1 and isNumberSign(words[0]):
                    line = "\n"
                    addIndent = False
                    emptyTitle = True

                # add indents,rst now reads the line as admonitions's content
                # since pandoc takes away indents when converting
                elif addIndent  and line.split() and not\
                        isNumberSign(words[0]):
                    #if end of line, add indent, strip original newline
                    # and add html newline character
                    if line.strip()[-1] == "*" or line.strip()[-1] == ".":
                        line = content (line) + " |br|\n"
                    #if not newline, just add idents and strip newline
                    else:
                        line = content (line)

                # Spot an admonition
                #length = 2 case is for Chinese space character
                elif (len(words) == 1 and words[0].replace("**", "").isalpha() \
                        and isAdmonition(words[0]) ) or\
                        (len(words) == 2 and isAdmonition(words[1])):
                    addIndent = True  # set addIndent to true
                    #making the title line
                    if len(words) == 1:
                        line = rstAdmonition (words[0])
                    else:
                        line = rstAdmonition (words[1])

                # Spot code block and language
                elif (len(words) == 2 and isCodeblock (words[0]))\
                        or (len(words) == 3 and isCodeblock (words[1])):

                    # while true, don't add Pandoc rst content to final rst
                    dontAdd = True
                    # while true, we are still in the code blok cotent
                    detected = True

                    # alter and add the title "code-block language" first
                    if len(words) == 2:
                        line = codeblockTitle(words[0], words[1])
                    else:
                        line = codeblockTitle(words[1], words[2])

                    input_file.write(line)

                    # new text file name
                    # code block from rst will be added to this text file
                    count = count + 1;
                    textFile = str(count) + ".txt"

                    # creating the new text file with the above name
                    codeFile = open(textFile, "a+")

                #detect a grid table
                elif  isEmptyLine(prevLine)\
                        and line.count("+") >= 2 and \
                        line.count("-") >= 2 and line.count("-+-") >= 1:
                    tableDetected = True

                #Spooting and take care of simple table headers
                if line.strip().replace("=","1").replace(" ", "2").isdigit()\
                        and  isEmptyLine(prevLine) \
                        and not tocDetected and not tableDetected:
                    sTableDetected = True

                #simple table that need title
                elif sTableDetected and line.count("**")>=4:
                    line = line + prevLine #add upper shell line ("===== ====")
                    sTableDetected = False

                #not a simple table that need title row
                elif sTableDetected and line.count("**")<=4:
                    sTableDetected = False

                #help with TOC deletion and spotting tables
                prevLine = line

                #adding the line to final rst file
                if tocDetected  or (dontAdd or
                                   addIndent  and isEmptyLine(line)):
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



if __name__ == "__main__":
    main()