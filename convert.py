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
-Spot and restore grid table without title row
-Spot and restore simple table with title row
-Spot and remove title from grid and simple table that not supposed
to have  a title row
-Applying title row to table that missing title row
-Delete the table of content that was originally in Word
-Fixing broken characters caused by double conversion
-Merging empty table cells
-Replace lonely hyphen in a cell with \-, so that it can be read as "-"
not "."

"""

import os
import sys
import re
import fileinput
import subprocess

def getListOfPortion (line, start, end):
    """
    Split a portion of the line, or check if that portion is empty
    :param line: Line to split
    :param start: start position
    :param end: end position
    :return: return a list of words, if line is empty, return False
    """
    return line[start: end].split()

def stripListOfPortion (line, start, end):
    """
    Strip a portion of the line, then split it (can't be reversed)
    :param line: Line to strip and split
    :param start: start position
    :param end: end position
    :return: return a list of words, if line is empty, return False
    """
    return line[start : end].strip().split()

def findOccurrences(s, ch):
    """
    Find positions that a character occurs  in a string
    :param s: string to check
    :param ch: character to find
    :return: list of integer -positions of the character
    """
    return [i for i, letter in enumerate(s) if letter == ch]

def getNextPosition (CellPositions, markPosition):
    """
    Get the next occuren of a character right after the mark apeared in
    the string
    :param CellPositions: list of positions that the character
     appear in the string
    :param markPosition: the mark
    :return: one position that character appears right after
     the mark position
    """
    for p in CellPositions:
        if p > markPosition:
            return p

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
    return word.strip().replace("*", "") == "#"


def isAdmonition (title):
    """
    Check if the line is the title of an admonition
    :param: the line to be checked
    :return: boolean- True if the line is the title of an admonition
    """
    # list of admonitions
    admonitions = ["attention", "caution", "danger", "hint", "tip",
                   "important", "note", "warning", "admonition","error"]

    return title.lower().replace("*", "").strip() in admonitions

def isTableEdge (line):

    return (line.count("+") >= 2 and \
                        line.count("-") >= 2 and line.count("-+-") >= 1) or\
           (line.count("+") >= 2 and \
                        line.count("=") >= 2 and line.count("=+=") >= 1)

def isSimpleTableEdge (line):
    return  line.strip().replace("=","1").replace(" ", "2").isdigit() and line.count("=")>= 3

def rstAdmonition (title):
    """
    Replacing the line with rst formatted admonition title
    :param title: the title line
    :return: string - title string with the correct rst format
    """
    return ".. " + title.lower().replace("*", "") + "::\n"


def isCodeblock (word):
    """
    Check if this is a start of code block
    :param word: the word to be checked
    :return: boolean- if this is the start of codeblock
    """
    return word.lower().replace("*", "").strip() == "code-block"


def codeblockTitle (title, language):
    """
    Replacing the line with rst formatted codeblock title
    :param title: string- code-block
    :param language: string- the language
    :return: string - codeblock title string with the correct rst format
    """
    return ".. " + title.lower().replace("*", "") + ":: " \
                           + language.replace("*", "") + "\n\n"


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
    return line.lower().replace("*", "").strip() == "table of contents"


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


    file = sys.argv[1]

    if file.split('.')[1] == "docx":

        command = "pandoc -s "+ file.split('.')[0]+".docx" +\
                  " -o "+ file.split('.')[0]+".rst" +" --extract-media=f "

        process = subprocess.Popen(command,
                                   stdout=subprocess.PIPE)
        output, error = process.communicate()

        file = file.split('.')[0]+".rst"

    count = 0 # for codeblock text file name
    addIndent = False  # if true, add indent to line for admonition content
    dontAdd = False  # don't add the line to result rst file
    detected = False  # a code block detected
    tocDetected = False #detect a toc to delete
    tableDetected = False #detect grid table
    noTitle = False #grid table with no title detected
    noSTitle = False
    prevLine = "" #keep track of previous line
    haveTitle = False #table should have title detected
    emptyTitle = False
    sTableDetected = False #simple table detected
    insideGrid = False #inside a grid table
    insideSimple = False #inside a simple table
    deletingGridCells = [] #position of | in the line to be deleted
    GfirstLineContent = False #first line of each row (except title row)
    SfirstLineContent = False # first content line of simple table
    lastGridTitle = False #the ending of title row
    cellUniform ="" #the cell format of a simple table exp === ===== ==
    skip = False #skip, don't check this line.
    # Used for gird table with multi lines - title
    simpleDeviders = [] # list of the divider positions of simple table.
    #exp: the position of empty spaces in === === ===

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

                line = line.replace('\u3000','')
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
                if noTitle and tableDetected and isTableEdge (line) and skip:
                    line = line.replace("=", "-")
                    noTitle = False
                    tableDetected = False
                    insideGrid = True
                    GfirstLineContent = True
                    lastGridTitle = True
                    skip = False

                #table should have a title
                elif haveTitle and tableDetected and isTableEdge (line) and skip:
                    line = line.replace("-", "=")
                    haveTitle = False
                    tableDetected = False
                    insideGrid = True
                    GfirstLineContent = True
                    lastGridTitle= True
                    skip = False

                # table without title found (no bold characters in first row)
                elif tableDetected  and "**" not in line and not skip:
                    noTitle = True
                    skip =True
                # table with title found
                # has more than 2 old characters in first row
                elif tableDetected  and line.count("**") >= 4 and not skip:
                    haveTitle = True
                    skip = True

                elif skip and not isTableEdge (line):
                    pass

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
                elif not insideSimple and \
                        (addIndent  and line.split() and not\
                        isNumberSign(words[0])):
                    #if end of line, add indent, strip original newline
                    # and add html newline character
                    if line.strip()[-1] == "*" or line.strip()[-1] == ".":
                        line = content (line) + " |br|\n"
                    #if not newline, just add idents and strip newline
                    else:
                        line = content (line)

                # Spot an admonition
                #length = 2 case is for Chinese space character
                elif not insideSimple and not insideGrid \
                        and ((len(words) == 1 and
                              words[0].replace("*", "").isalpha() \
                              and isAdmonition(words[0])) or \
                             (len(words) == 2 and isAdmonition(words[1]) and
                              ((len(words[0].strip()) == 3 and
                                words[0][1] == "*" and words[0][0] == "*") or
                               (len(words[0].strip()) == 2 and
                                words[0][0] == "*"
                                and not words[0][1].isalnum())
                               or (len(words[0].strip()) == 1
                               and not words[0][0].isalnum() )))):

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

                #Spotting and take care of simple table headers
                if line.strip().replace("=","1").replace(" ", "2").isdigit()\
                        and  isEmptyLine(prevLine) \
                        and not tocDetected and not tableDetected:
                    sTableDetected = True
                    cellUniform = line

                #simple table that need title
                elif sTableDetected and line.count("**")>=4:
                    line = line + prevLine #add upper Cell line ("===== ====")
                    sTableDetected = False
                    insideSimple = True
                    SfirstLineContent = True

                elif noSTitle:
                    line = line.replace("=","")
                    if not line.split():
                        line = ""
                    sTableDetected = False
                    insideSimple = True
                    SfirstLineContent = True
                    noSTitle = False

                #not a simple table that need title row
                elif sTableDetected and line.count("**")<=4:
                    noSTitle = True

                #inside grid table
                if insideGrid :
                    #the first line in the content area of the table
                    if GfirstLineContent and not lastGridTitle:

                        if (line.split()):
                            #list of positions of |
                            cellPositions = findOccurrences(line, '|')

                            #go through each positions
                            for index in range (0, len(cellPositions)):
                                if index < len(cellPositions) - 1:

                                    #if the portion of the line from
                                    # this position to the next position
                                    #is empty
                                    #allowing at least 3 spaces
                                    # between the two |
                                    # to considered empty
                                    if not getListOfPortion (line,
                                            cellPositions[index]+1,
                                             cellPositions[index+1]) and \
                                            cellPositions[index + 1] - \
                                            cellPositions[index] > 3:

                                        #store the index of the position
                                        # in a list,
                                        # to delete the position later
                                        if (cellPositions[index]!=0 and
                                                cellPositions[index]!=1):
                                            deletingGridCells.append\
                                                (cellPositions[index])

                                    #found a portion that only has a "-"
                                    elif getListOfPortion (line,
                                         cellPositions[index]+1,
                                        cellPositions[index+1]) and\
                                            len(stripListOfPortion (line,
                                         cellPositions[index]+1,
                                        cellPositions[index+1]) ) == 1 and \
                                            stripListOfPortion(line,
                                                        cellPositions[
                                                        index] + 1,
                                                        cellPositions[
                                                        index + 1])[0] == "-" :

                                        #hyphen's position
                                        # relative to the line
                                        hyphenPositionList = \
                                            findOccurrences(line, '-')

                                        #the position of the | that
                                        # occurs right after hyphen
                                        hyphenPosition = getNextPosition\
                                            (hyphenPositionList,
                                             cellPositions[index])

                                        #replace the lonely hyphen
                                        # in table with "\-"
                                        line = line[:hyphenPosition] + "\-" + \
                                               line[hyphenPosition + 2:]

                            #go through positions to be deleted
                            # and replace them
                            if len (deletingGridCells) >= 1:
                                for i in deletingGridCells:
                                    line = line[:i] + " " + line[i + 1:]

                        else:
                            insideGrid = False
                            deletingGridCells.clear()

                        GfirstLineContent = False

                    #pass the title row, go to the first table cell after title
                    elif GfirstLineContent and  lastGridTitle:
                        lastGridTitle = False

                    #go through each line in table to merge epty cells
                    elif not isTableEdge (line) and len(deletingGridCells)>= 1\
                            and not GfirstLineContent:

                        for i in deletingGridCells:
                            line = line[:i] + " " + line[i + 1:]

                    #end of a row, go to the next row
                    elif isTableEdge(line):
                        deletingGridCells.clear()
                        GfirstLineContent = True

                    #done with this table, got out of the table
                    elif  isTableEdge(prevLine) and not line.split():
                        insideGrid = False
                        GfirstLineContent = False
                        deletingGridCells.clear()



                #Inside simple table
                if insideSimple and not isSimpleTableEdge (line):

                    if SfirstLineContent:
                        #cells of simple table has the same == === shape
                        #cellUniform is the uniform shape

                        #get all positions of = in the cell line
                        aligns = findOccurrences(cellUniform, '=')

                        #add first position to this list of positions
                        #of beginning and endding of each column
                        #exp:
                        # this list will have values of these positions
                        # === ====
                        # 0 2 3  6
                        simpleDeviders.append(0)
                        for p in range (0,len(aligns)):
                            if p < len(aligns )-1:
                                if aligns[p+1] - aligns[p] > 1:
                                    simpleDeviders.append(aligns[p+1])
                        #add last position to the list
                        simpleDeviders.append(len(aligns))
                        SfirstLineContent = False

                    #for the table content lines
                    elif not SfirstLineContent:

                        #if there are at least 2 columns
                        if len(simpleDeviders ) >=3:

                            for i in range (0,len(simpleDeviders)-1):

                                #find the col of the row that only has -
                                if getListOfPortion (line,simpleDeviders[i],
                                                     simpleDeviders[
                                    i + 1]) and \
                                len(stripListOfPortion (line,simpleDeviders[i],
                                                     simpleDeviders[
                                    i + 1]) ) == 1 and \
                                        stripListOfPortion(line,
                                                         simpleDeviders[i],
                                                         simpleDeviders[
                                                             i + 1])[0] == "-":
                                    #position of the "-"
                                    # relative to the portion
                                    # (in that col of the row)
                                    # exp:
                                    # === ===
                                    #      -
                                    #return 1
                                    hyphenInPortion = findOccurrences\
                                        (line[simpleDeviders[i]:
                                              simpleDeviders[i + 1]], '-')

                                    # position of the "-"
                                    # relative to the line
                                    # exp:
                                    # === ===
                                    #      -
                                    # return 5
                                    hyphenIndex = simpleDeviders[i] +\
                                                  hyphenInPortion[0]

                                    #replace - with \-
                                    line = line[:hyphenIndex] + "\-" +\
                                           line[ hyphenIndex + 1:]

                #Done with this table, got out of the table
                elif insideSimple and isSimpleTableEdge (line):
                    insideSimple = False
                    simpleDeviders.clear()
                    SfirstLineContent = False


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

