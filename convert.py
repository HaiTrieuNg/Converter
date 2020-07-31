import os
import sys
import fileinput
import subprocess

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
dontAdd = False
detected = False
done_writing_to_file = False

try:

    with open(file, 'r+', encoding='UTF-8') as input_file:
        input_file.write (".. |br| raw:: html\n\n"+"     <br/>\n\n")

        for line in fileinput.FileInput(file):

            #list of words in the line
            words = line.split()

            #done writing to file
            if detected is True \
                    and (len(words) == 1 and words[0].strip() == "#"):
                detected = False
                codeFile.close()



                #do something here to change the codeblock text file with indents

                command = "astyle --style=allman " + textFile
                process = subprocess.Popen(command,
                                           stdout=subprocess.PIPE)
                output, error = process.communicate()

                #try:
                #    with open(textFile, 'a+',
                 #             encoding='UTF-8') as codeblock_file:
                 #       codeblock_file.write("I was reopened")
                #        codeblock_file.close()
                #except FileNotFoundError as error:
                    # if the file can't be found
                #   print(error)




                #Then write it to the result rst
                # writing from text file to rst
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




            elif detected is True  and (len(words) != 0 and words[0].strip() != "#"):
                codeFile.write(line)

            if dontAdd is True and len(words) == 1 \
                and words[0].strip() == "#" :
                dontAdd = False

            # take care of broken character caused by double conversion
            if line.split() or (len(words) == 1 \
                and words[0].strip() != "#") :
                for key in replacing_dict:
                    if key in line:
                        line = line.replace(key, replacing_dict[key])

            #use # to mark the need of a newline
            #since pandoc deletes all newlines when converting
            if len(words) == 1 and words[0].strip() == "#":
                line = "\n"
                addIndent = False

            #add indents,rst now reads the line as admonitions's content
            #since pandoc takes away indents when converting
            elif addIndent is True and line.split() and words[0].strip() != "#":
                line = "     " + line.strip() + " |br|\n"


            #Spot an admonition
            elif len(words) == 1 and words[0].replace("**","").isalpha() \
                    and words[0].lower().replace("**","") in admonitions:
                addIndent = True #set addIndent to true
                line = ".. " + words[0].lower().replace("**","") + "::\n"

            #Spot code block and language
            elif len(words) == 2 and \
                    words[0].lower().replace("**","") == "code-block":
                dontAdd = True
                detected = True
                line = ".. " + words[0].lower().replace("**","") + ":: "\
                            + words[1].replace("**","")+ "\n\n"

                input_file.write(line)

                print("Codeblock detected, please enter a text file path")

                count = count + 1;
                textFile = str(count) + ".txt"

                #adding to text file
                codeFile = open(textFile, "a+")


            #delete the extra empty lines caused by
            # converting from Word to rst
            if (dontAdd is True or
                addIndent is True and len(words) == 1 and
                words[0] == "|br|") or \
                (addIndent is True and not line.strip()) :
                pass
            else:
            #add the lines to the file
                input_file.write(line)

    input_file.close()
    print ("The task is completed.")

except FileNotFoundError as error:
    # if the file can't be found
    print(error)



