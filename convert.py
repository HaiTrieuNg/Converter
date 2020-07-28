import os
import sys
import fileinput

print ("Please enter a file path with format: path\ filename.rst")

file= input( ">>" )

#list of admonitions
admonitions = ["attention", "caution", "danger", "error", "hint", "tip",
               "important", "note", "warning", "admonition", "code"]

replacing_dict = {
    'â€“': "—",
    "â€”": "–",
    "â€˜": "‘",
    "â€™": "’",
    "â€œ": "“",
    "â€": "”",
}
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

            #take care of broken character caused by double conversion
            for w in words:
                for key in replacing_dict:
                    if key in w:
                        w = w.replace(key,replacing_dict[key])

            #use # to mark the need of a newline
            #since pandoc deletes all newlines when converting
            if len(words) == 2 and words[0].strip() == "#":
                line = "\n"
                addIndent = False

            #Spot an admonition
            elif len(words) == 1 and words[0].replace("**","").isalpha() \
                    and words[0].lower().replace("**","") in admonitions:
                addIndent = True #set addIndent to true
                line = ".. " + words[0].lower().replace("**","") + "::\n"

            #Spot code block and language
            elif len(words) == 2 and \
                    words[0].lower().replace("**","") == "code-block":
                addIndent = True
                noNewLine = True
                line = ".. " + words[0].lower().replace("**","") + ":: "\
                            + words[1].replace("**","")+ "\n\n"

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



