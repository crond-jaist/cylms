"""
yamlParser.py
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils import dir_util
from distutils.errors import DistutilsFileError
from shutil import copy2
#import zipfile
import os
import sys
import ConfigParser
import io
import codecs
import re
import logging
import yaml

from storyboard import Storyboard

logging.basicConfig(level=logging.DEBUG, \
#                    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
                    format='* %(levelname)s: %(filename)s: %(message)s')

TEMPLATE_DIR = 'Template' # Template SCORM package

#Enable if you need to debug the content
debug = 0

def addQuestion(questionFile,questionFileTemporary,questionId,questionBody,\
                questionType,questionAnswer,questionCorrectAnswer,questionHints):

    #Define objective ID of training (by default is obj_playing, do not change it)
    questionObjectiveId = """obj_playing"""

    if questionType == Storyboard.VALUE_TYPE_FILL_IN: questionType = 'QUESTION_TYPE_FILL'
    elif questionType == Storyboard.VALUE_TYPE_NUMERIC: questionType = 'QUESTION_TYPE_NUMERIC'
    elif questionType == Storyboard.VALUE_TYPE_CHOICE: questionType = 'QUESTION_TYPE_CHOICE' 

    hints = []
    if questionHints:
        for hint in questionHints:
            #logging.debug("Question hint: " + hint)
            # Need to check type both for string and unicode (for JA support)
            if type(hint) == str or type(hint) == unicode:
                hints.append(hint)
            else:
                logging.error("Incorrect format for hint string: " + repr(hint).decode("unicode-escape"))
                quit(-1)
    else:
        # If the value is None, it means the 'hints' tag was used, so we return error;
        # otherwise the value is an empty string, meaning the 'hints' tag was not used,
        # hence we do nohing
        if questionHints is None:
            logging.error("No strings provided in the 'hints' array.")
            quit(-1)

    my_f = io.open(questionFile,'r',encoding='utf8')
    temp = io.open(questionFileTemporary,'ab')

    #Replace content in template file
    content = my_f.read().encode('utf-8')
    #Convert int to unicode
    temp_list = [questionId,questionBody,questionType,questionAnswer,questionCorrectAnswer,questionObjectiveId]
    for counter, i in enumerate(temp_list):
        if isinstance(i, int): 
            temp_list[counter] = str(i).encode('utf-8') 
    questionId,questionBody,questionType,questionAnswer,questionCorrectAnswer,questionObjectiveId = temp_list
    #Change symbol " to \" to avoid errors in HTML, then avoid the case \\
    questionId = questionId.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    questionBody = questionBody.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    questionType = questionType.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    # The actual output to JavaScript file will be built later, here we just convert to UTF-8
    questionAnswer = questionAnswer.encode('utf-8')
    questionCorrectAnswer = questionCorrectAnswer.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    questionObjectiveId = questionObjectiveId.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    for i in range(0,len(hints)):
        hints[i] = hints[i].encode('utf-8').replace('"','\\"').replace('\\\\','\\')

    # Question type choice is a special case, while we need to put choices in an array
    
    if questionType == 'QUESTION_TYPE_CHOICE':
        content = content.replace('questionAnswer','new Array(questionAnswer)')
    for i in range(0,len(hints)):
        content = content.replace('questionHint'+str(i+1),hints[i])
    content = re.sub('".*questionHint.*"','""',content)

    # Create choice data appropriate for inclusion in JavaScript file
    choiceData = buildChoiceData(questionAnswer)

    content = content.replace(Storyboard.TAG_QUESTION_ID, str(questionId))
    content = content.replace(Storyboard.TAG_QUESTION_BODY, str(questionBody))
    content = content.replace(Storyboard.TAG_QUESTION_TYPE, str(questionType))
    content = content.replace(Storyboard.TAG_QUESTION_ANSWER, str(choiceData))
    content = content.replace(Storyboard.TAG_QUESTION_CORRECT_ANSWER, str(questionCorrectAnswer))
    content = content.replace(Storyboard.TAG_QUESTION_OBJECTIVE_ID, str(questionObjectiveId))

    if debug == 1: print content
    temp.write(content)
    my_f.close()
    temp.close()

# Build choice data appropriate for inclusion in JavaScript file
def buildChoiceData(questionAnswer):

    # Initialize to default value for fill-in questions
    choiceData = "null"

    # Deal with options for multiple-choice questions
    if questionAnswer != "null":

        # Initialize processed option list
        optionList2 = []

        # Split options by comma
        optionList = questionAnswer.split(",")

        # Process options
        for option in optionList:
            # Remove white spaces at beginning and end of string
            option = option.strip()

            # Make basic check for double quote prefix/suffix
            if (option.startswith('"') and not option.endswith('"')) or (not option.startswith('"') and option.endswith('"')):
                logging.error("Incorrect use of double quote symbols for option: " + option)
                quit(-1)

            # Add double quote prefix or suffix if needed
            if not option.startswith('"') and not option.endswith('"'):
                option = '"' + option + '"'
            
            # Append option to processed option list
            optionList2.append(option)

        # Build choice data string
        choiceData = ""
        for option in optionList2:
            choiceData += (str(option) + ",")

        # Remove last unnecessary comma 
        choiceData=choiceData[:-1]

    #logging.debug("buildChoiceData: choiceData='" + choiceData + "'")

    return choiceData


def addInformation(startFile, startFileTemporary, manifestFile, manifestFileTemporary, 
                   id, description, header, level):

    # Write description information to template manifestFile
    file = io.open(manifestFile,'r')
    temp = io.open(manifestFileTemporary,'ab')

    content = file.read()
    idText = str(id)
    content = content.replace(Storyboard.TAG_TRAINING_ID, idText.encode('utf-8'))

    if debug == 1: print content
    temp.write(content)
    file.close()
    temp.close()

    # Write description information to template startFile
    file = io.open(startFile,'r')
    temp = io.open(startFileTemporary,'ab')

    content = file.read().encode('utf-8')
    # Build the level text
    if level:
        levelText = "Level {0}: ".format(str(level).encode('utf-8'))
    else:
        levelText = ""
    content = content.replace(Storyboard.TAG_TRAINING_LEVEL, levelText.encode('utf-8'))
    content = content.replace(Storyboard.TAG_TRAINING_TITLE, description.encode('utf-8'))
    content = content.replace(Storyboard.TAG_TRAINING_OVERVIEW, header.encode('utf-8'))

    if debug == 1: print content
    temp.write(content)
    file.close()
    temp.close()


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file)) 

# Get option from configuration file (return None if option is not present)
def getOption(config_file, option):
    Config = ConfigParser.ConfigParser()
    Config.read(config_file)
    if Config.has_option(Storyboard.CONFIG_SECTION, option):
        if option == Storyboard.CONFIG_ENABLE_COPY:
            return Config.getboolean(Storyboard.CONFIG_SECTION, option)
        else:
            return Config.get(Storyboard.CONFIG_SECTION, option)
    else:
        return None

#####################################################################
## START MAIN FUNCTION ##
def yamlToSCORM(config_file, dir_path):

    # NOTE: This parsing only works with YAML structure with 1 question set

    input_file = getOption(config_file, Storyboard.CONFIG_INPUT_FILE)
    if input_file:
        logging.info("Parse input file: " + input_file)
    else:
        logging.error("Setting for '{}' missing in configuration file '{}'.".format(Storyboard.CONFIG_INPUT_FILE, config_file))
        quit(-1)

    # Build sets with valid keys for training and question sections
    valid_training_keys = set([Storyboard.KEY_ID, Storyboard.KEY_TITLE, Storyboard.KEY_OVERVIEW, Storyboard.KEY_LEVEL, Storyboard.KEY_QUESTIONS])
    valid_question_keys = set([Storyboard.KEY_ID, Storyboard.KEY_TYPE, Storyboard.KEY_BODY, Storyboard.KEY_CHOICES, Storyboard.KEY_ANSWER, Storyboard.KEY_HINTS])

    try:
        with codecs.open(input_file, 'r', 'utf-8') as stream:
            output = yaml.load(stream)
            if debug: print output
            if not output:
                logging.error("No data in the input file: " + input_file)
                quit(-1)
            for i in output:
                if type(i) != dict:
                    logging.error("Incorrect format in the input file: " + input_file)
                    quit(-1)
                for j in i:
                    # Check that top-level tag matches 'training'
                    if j != Storyboard.KEY_TRAINING:
                        logging.error("Top-level section in training content does not match '{0}': {1}".format(Storyboard.KEY_TRAINING, j))
                        quit(-1)

                    # Process tags within training section
                    for k in i[j]:
                        # Store dictionary in global variable (why?)
                        #info_dict = dict(k)

                        # Check whether any unknown tags are present
                        training_keys = set(k.keys())
                        unknown_training_keys = training_keys.difference(valid_training_keys)
                        if unknown_training_keys:
                            logging.error("Unknown tags found in training content: " + repr(unknown_training_keys))
                            quit(-1)

                        # Check existence of required fields in training section
                        if Storyboard.KEY_ID not in k:
                            logging.error("Required field in training content is missing: " + Storyboard.KEY_ID)
                            quit(-1)
                        if Storyboard.KEY_TITLE not in k:
                            logging.error("Required field in training content is missing: " + Storyboard.KEY_TITLE)
                            quit(-1)
                        if Storyboard.KEY_OVERVIEW not in k:
                            logging.error("Required field in training content is missing: " + Storyboard.KEY_OVERVIEW)
                            quit(-1)
                        if Storyboard.KEY_QUESTIONS not in k:
                            logging.error("Required field in training content is missing: " + Storyboard.KEY_QUESTIONS)
                            quit(-1)

                        # If optional field 'level' is not found in the input file, we provide 
                        # a default value for it
                        if Storyboard.KEY_LEVEL not in k:
                            k[Storyboard.KEY_LEVEL] = None

                        # Define training name and make new package folder for new SCORM package
                        training_name = k[Storyboard.KEY_ID]

                        # Change the training name to the full path directory:
                        training_name = str(dir_path) + "/" + str(training_name)

                        # Copy from the template package to the new package
                        try:
                            dir_util.copy_tree((str(dir_path) + "/" + TEMPLATE_DIR), training_name)
                        except DistutilsFileError as e:
                            logging.error("Issue when copying template: " + str(e))
                            quit(-1)

                        # Add questions to temporary file
                        # Work flow: get template from question.js, fill in the content for each question and add one by one question into temporary file. After finish, replace question.js by the temporary file and delete the temporary one.
                        question_file = training_name + '/Playing/questions.js'
                        question_file_temporary = question_file + '_temporary'

                        # Process questions
                        for question in k[Storyboard.KEY_QUESTIONS]:

                            # Check whether any unknown tags are present
                            question_keys = set(question.keys())
                            unknown_question_keys = question_keys.difference(valid_question_keys)
                            if unknown_question_keys:
                                logging.error("Unknown tags found in question section: " + repr(unknown_question_keys))
                                quit(-1)

                            # Check existence of required fields in question section
                            if Storyboard.KEY_ID not in question:
                                logging.error("Required field in question section is missing: " + Storyboard.KEY_ID)
                                quit(-1)
                            if Storyboard.KEY_BODY not in question:
                                logging.error("Required field in question '{0}' section is missing: {1}".format(question[Storyboard.KEY_ID], Storyboard.KEY_BODY))
                                quit(-1)
                            if Storyboard.KEY_ANSWER not in question:
                                logging.error("Required field in question '{0}' section is missing: {1}".format(question[Storyboard.KEY_ID], Storyboard.KEY_ANSWER))
                                quit(-1)

                            # Determine the question type if it was not set already via the optional 
                            # field 'type' 
                            if Storyboard.KEY_TYPE not in question:
                                # Question type is 'choice' if 'choices' field is present, 'fill-in' otherwise
                                if Storyboard.KEY_CHOICES in question:
                                    question[Storyboard.KEY_TYPE] = Storyboard.VALUE_TYPE_CHOICE
                                else:
                                    question[Storyboard.KEY_TYPE] = Storyboard.VALUE_TYPE_FILL_IN

                            # Verify validity of description
                            # Fill-in questions cannot have choices field
                            if question[Storyboard.KEY_TYPE] == Storyboard.VALUE_TYPE_FILL_IN and Storyboard.KEY_CHOICES in question:
                                logging.error("Fill-in type questions cannot have a '{0}' field.".format(Storyboard.KEY_CHOICES))
                                quit(-1)
                            if question[Storyboard.KEY_TYPE] == Storyboard.VALUE_TYPE_CHOICE and Storyboard.KEY_CHOICES not in question:
                                logging.error("Fill-in type questions must have a '{0}' field.".format(Storyboard.KEY_CHOICES))
                                quit(-1)                             

                            # If a question has no 'choices' field, then we set it to 'null' 
                            # so that it is dealt with appropriately in JavaScript
                            if Storyboard.KEY_CHOICES not in question:
                                question[Storyboard.KEY_CHOICES] = "null"
                  
                            # If optional field 'hints' is not provided, we set it to ''
                            if Storyboard.KEY_HINTS not in question:
                                question[Storyboard.KEY_HINTS] = ""

                            # Actually add the question to the internal data structure
                            addQuestion(question_file, question_file_temporary, question[Storyboard.KEY_ID], question[Storyboard.KEY_BODY], question[Storyboard.KEY_TYPE], question[Storyboard.KEY_CHOICES], question[Storyboard.KEY_ANSWER], question[Storyboard.KEY_HINTS])

                        #Replace question.js by temporary file
                        copy2(question_file_temporary,question_file)
                        os.remove(question_file_temporary)

                        #Add information about level, header and description
                        start_file = training_name + '/shared/assessmenttemplate.html'
                        start_file_temporary = start_file + '_temporary'
                        manifest_file = training_name + '/imsmanifest.xml'
                        manifest_file_temporary = manifest_file + '_temporary'
                         
                        addInformation(start_file, start_file_temporary, manifest_file, manifest_file_temporary, k[Storyboard.KEY_ID], k[Storyboard.KEY_TITLE], k[Storyboard.KEY_OVERVIEW], k[Storyboard.KEY_LEVEL])
                        #Replace start.html by temporary file
                        copy2(start_file_temporary,start_file)
                        os.remove(start_file_temporary)
                        #Replace imsmanifest.xml by temporary file
                        copy2(manifest_file_temporary,manifest_file)
                        os.remove(manifest_file_temporary)
                        
                        # Create SCORM package
                        package_name = getOption(config_file, Storyboard.CONFIG_PACKAGE_NAME)
                        if package_name:
                            logging.info("Create SCORM package: " + package_name)
                            os.system("cd %s; zip -q -r %s *" %(training_name, package_name))
                        else:
                            logging.error("Setting for '{}' missing in configuration file '{}'.".format(Storyboard.CONFIG_PACKAGE_NAME, config_file))
                            quit(-1)

    except (IOError, yaml.YAMLError) as e:
        logging.error(e)
        quit(-1)


def main():
    #Get the directory of the program:
    dir_path = os.path.dirname(os.path.realpath(__file__))

    #Print banner
    #Read version from a readme file
    readme = 'readme'
    readme = str(dir_path) + "/" + readme

    f = open(readme)
    for line in f:
        if re.match('version',line.lower()):
            VERSION = line.rstrip('\n')
            break


    logging.info("#########################################################################")
    logging.info("cnt2lms %s: Training content to LMS converter - parser" % (VERSION)) 
    logging.info("#########################################################################")
    
    config = "config"   

    config = str(dir_path) + "/" + config

    #Input yaml file
    try:
        config = sys.argv[1]
    except:
        logging.info("Please specify a configuration file. Example: ./yamlParser.py my_config")
        logging.info("Using default configuration file: " + str(config))
    yamlToSCORM(config, dir_path)

if __name__ == "__main__":
    main()

