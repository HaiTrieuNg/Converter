import os
import sys
import fileinput

print ("Please enter a file path with format: path\ filename.rst")

file= input( ">>" )

#list of admonitions
admonitions = ["attention", "caution", "danger", "error", "hint", "tip",
               "important", "note", "warning", "admonition", "code"]

addIndent = False #if this set to true, add indent to the line
noNewLine = False

try:

    with open(file, 'r+', encoding='UTF-8') as input_file:
        input_file.write (".. |br| raw:: html\n\n"+"     <br/>\n\n")

        for line in fileinput.FileInput(file):

            #add indents,rst now reads the line as admonitions's content
            #since pandoc takes away indents when converting
            if addIndent is True and noNewLine is False:
                line = "     " + line.strip() + " |br|\n"
            #newline markup |br| is not needed for code block
            elif addIndent is True and noNewLine is True:
                line = "     " + line

            #list of words in the line
            words = line.split()

            #use # to mark the need of a newline
            #since pandoc deletes all newlines when converting
            if len(words) == 2 and words[0] == "#":
                line = "\n"
                addIndent = False

            #Spot an admonition
            elif len(words) == 1 and words[0].isalpha() \
                    and words[0].lower() in admonitions:
                addIndent = True #set addIndent to true
                line = ".. " + words[0].lower() + "::\n"

            #Spot code block and language
            elif len(words) == 2 and words[0].lower() == "code-block":
                addIndent = True
                noNewLine = True
                line = ".. " + words[0].lower() + ":: "\
                            + words[1]+ "\n\n"

            #delete the extra empty lines caused by
            # converting from Word to rst
            if (addIndent is True and len(words) == 1 and
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



