#!/usr/bin/env python

#############################################################################
# Content to LMS converter for CyLMS
#############################################################################

# External imports
from distutils import dir_util
from distutils.errors import DistutilsFileError
from shutil import copy2
import os
import io
import codecs
import re
import logging
import yaml
import sys

# Internal imports
from storyboard import Storyboard

# Constants
TEMPLATE_DIR = 'Template' # Template SCORM package


#############################################################################
# Functions
#############################################################################

# TODO: Use class below instead of just functions
# TODO: Verify return value of called functions and act accordingly


#############################################################################
# Add question to question file in SCORM package
def addQuestion(questionFile,questionFileTemporary,questionId,questionBody,\
                questionType,questionAnswer,questionCorrectAnswer,questionHints):

    # Define objective ID of training (by default is obj_playing, do not change it)
    questionObjectiveId = """obj_playing"""

    if questionType == Storyboard.VALUE_TYPE_FILL_IN: questionType = 'QUESTION_TYPE_FILL'
    elif questionType == Storyboard.VALUE_TYPE_NUMERIC: questionType = 'QUESTION_TYPE_NUMERIC'
    elif questionType == Storyboard.VALUE_TYPE_CHOICE: questionType = 'QUESTION_TYPE_CHOICE' 

    hints = []
    if questionHints:
        for hint in questionHints:
            logging.debug("Question hint: " + hint)
            # Need to check type both for string and unicode (for JA support)
            if type(hint) == str or type(hint) == unicode:
                hints.append(hint)
            else:
                logging.error("Incorrect format for hint string: " + repr(hint).decode("unicode-escape"))
                return False
    else:
        # If the value is None, it means the 'hints' tag was used, so we return error;
        # otherwise the value is an empty string, meaning the 'hints' tag was not used,
        # hence we do nohing
        if questionHints is None:
            logging.error("No strings provided in the 'hints' array.")
            return False

    my_f = io.open(questionFile,'r',encoding='utf8')
    temp = io.open(questionFileTemporary,'ab')

    # Replace content in template file
    content = my_f.read().encode('utf-8')
    # Convert int to unicode
    temp_list = [questionId,questionBody,questionType,questionAnswer,questionCorrectAnswer,questionObjectiveId]
    for counter, i in enumerate(temp_list):
        if isinstance(i, int): 
            temp_list[counter] = str(i).encode('utf-8') 
    questionId,questionBody,questionType,questionAnswer,questionCorrectAnswer,questionObjectiveId = temp_list
    # Change symbol " to \" to avoid errors in HTML, then avoid the case \\
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

    logging.debug("Content: "+content)
    temp.write(content)
    my_f.close()
    temp.close()

    return True


#############################################################################
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
                return None

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

    logging.debug("buildChoiceData: choiceData='" + choiceData + "'")

    return choiceData


#############################################################################
# Add information not related to questions to auxiliary SCORM package files
def addInformation(startFile, startFileTemporary, manifestFile, manifestFileTemporary, 
                   id, description, header, level):

    # Write description information to template manifestFile
    file = io.open(manifestFile,'r')
    temp = io.open(manifestFileTemporary,'ab')

    content = file.read()
    idText = str(id)
    content = content.replace(Storyboard.TAG_TRAINING_ID, idText.encode('utf-8'))

    logging.debug("Content: " + content)
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

    logging.debug("Content: " + content)
    temp.write(content)
    file.close()
    temp.close()

#def zipdir(path, ziph):
#    # ziph is zipfile handle
#    for root, dirs, files in os.walk(path):
#        for file in files:
#            ziph.write(os.path.join(root, file)) 

#########################################################################
# Convert training content description in YAML format to a SCORM package;
# if absolute path is not provided, the SCORM file is saved in the program path
# NOTE: Currently this function only supports YAML files with one question set
def yaml2scorm(input_file, scorm_file, program_path):

    # Check whether input file was provided
    if input_file:
        logging.info("Process training content file '{}'.".format(input_file))
    else:
        logging.error("Training content file invalid: {}.".format(input_file))
        return False

    # Build sets with valid keys for training and question sections
    valid_training_keys = set([Storyboard.KEY_ID, Storyboard.KEY_TITLE, Storyboard.KEY_OVERVIEW,
                               Storyboard.KEY_LEVEL, Storyboard.KEY_QUESTIONS])
    valid_question_keys = set([Storyboard.KEY_ID, Storyboard.KEY_TYPE, Storyboard.KEY_BODY,
                               Storyboard.KEY_CHOICES, Storyboard.KEY_ANSWER, Storyboard.KEY_HINTS])

    try:
        with codecs.open(input_file, 'r', 'utf-8') as stream:
            output = yaml.load(stream)
            logging.debug("YAML file: " + str(output))
            if not output:
                logging.error("No data in the input file: " + input_file)
                return False
            for i in output:
                if type(i) != dict:
                    logging.error("Incorrect format in the input file: " + input_file)
                    return False
                for j in i:
                    # Check that top-level tag matches 'training'
                    if j != Storyboard.KEY_TRAINING:
                        logging.error("Top-level section in training content does not match '{0}': {1}".format(Storyboard.KEY_TRAINING, j))
                        return False

                    # Process tags within training section
                    for k in i[j]:

                        # Check whether any unknown tags are present
                        training_keys = set(k.keys())
                        unknown_training_keys = training_keys.difference(valid_training_keys)
                        if unknown_training_keys:
                            logging.error("Unknown tags found in training content: " + repr(unknown_training_keys))
                            return False

                        # Check existence of required fields in training section
                        if Storyboard.KEY_ID not in k:
                            logging.error("Required field in training content is missing: " + Storyboard.KEY_ID)
                            return False
                        if Storyboard.KEY_TITLE not in k:
                            logging.error("Required field in training content is missing: " + Storyboard.KEY_TITLE)
                            return False
                        if Storyboard.KEY_OVERVIEW not in k:
                            logging.error("Required field in training content is missing: " + Storyboard.KEY_OVERVIEW)
                            return False
                        # Although questions are in principle not optional, we allow content descriptions without
                        # questions in order to have more flexibility (e.g., to generate default content)
                        #if Storyboard.KEY_QUESTIONS not in k:
                        #    logging.error("Required field in training content is missing: " + Storyboard.KEY_QUESTIONS)
                        #    return False

                        # If optional field 'level' is not found in the input file, we provide 
                        # a default value for it
                        if Storyboard.KEY_LEVEL not in k:
                            k[Storyboard.KEY_LEVEL] = None

                        # Define training name and make new package folder for new SCORM package
                        training_name = k[Storyboard.KEY_ID]

                        # Change the training name to the full path directory:
                        training_name = str(program_path) + "/" + str(training_name)

                        # Copy from the template package to the new package
                        try:
                            dir_util.copy_tree((str(program_path) + "/" + TEMPLATE_DIR), training_name)
                        except DistutilsFileError as e:
                            logging.error("Issue when copying template: " + str(e))
                            return False

                        # Add questions to temporary file
                        # Workflow: get template from question.js, fill in the content for each question and
                        # add one by one question into temporary file. After finish, replace question.js by
                        # the temporary file and delete the temporary one.
                        question_file = training_name + '/Playing/questions.js'
                        question_file_temporary = question_file + '_temporary'

                        # Process questions
                        if Storyboard.KEY_QUESTIONS in k:
                            for question in k[Storyboard.KEY_QUESTIONS]:

                                # Check whether any unknown tags are present
                                question_keys = set(question.keys())
                                unknown_question_keys = question_keys.difference(valid_question_keys)
                                if unknown_question_keys:
                                    logging.error("Unknown tags found in question section: " + repr(unknown_question_keys))
                                    return False

                                # Check existence of required fields in question section
                                if Storyboard.KEY_ID not in question:
                                    logging.error("Required field in question section is missing: " + Storyboard.KEY_ID)
                                    return False
                                if Storyboard.KEY_BODY not in question:
                                    logging.error("Required field in question '{0}' section is missing: {1}"
                                                  .format(question[Storyboard.KEY_ID], Storyboard.KEY_BODY))
                                    return False
                                if Storyboard.KEY_ANSWER not in question:
                                    logging.error("Required field in question '{0}' section is missing: {1}"
                                                  .format(question[Storyboard.KEY_ID], Storyboard.KEY_ANSWER))
                                    return False

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
                                    return False
                                if question[Storyboard.KEY_TYPE] == Storyboard.VALUE_TYPE_CHOICE and Storyboard.KEY_CHOICES not in question:
                                    logging.error("Fill-in type questions must have a '{0}' field.".format(Storyboard.KEY_CHOICES))
                                    return False

                                # If a question has no 'choices' field, then we set it to 'null' 
                                # so that it is dealt with appropriately in JavaScript
                                if Storyboard.KEY_CHOICES not in question:
                                    question[Storyboard.KEY_CHOICES] = "null"

                                # If optional field 'hints' is not provided, we set it to ''
                                if Storyboard.KEY_HINTS not in question:
                                    question[Storyboard.KEY_HINTS] = ""

                                # Actually add the question to the internal data structure
                                addQuestion(question_file, question_file_temporary, question[Storyboard.KEY_ID],
                                            question[Storyboard.KEY_BODY], question[Storyboard.KEY_TYPE],
                                            question[Storyboard.KEY_CHOICES], question[Storyboard.KEY_ANSWER],
                                            question[Storyboard.KEY_HINTS])

                        # Only copy the temporary question file if there were some questions to start with
                        if Storyboard.KEY_QUESTIONS in k:
                            # Replace question.js by temporary file
                            copy2(question_file_temporary,question_file)
                            os.remove(question_file_temporary)

                        # Add information about level, header and description
                        start_file = training_name + '/shared/assessmenttemplate.html'
                        start_file_temporary = start_file + '_temporary'
                        manifest_file = training_name + '/imsmanifest.xml'
                        manifest_file_temporary = manifest_file + '_temporary'

                        addInformation(start_file, start_file_temporary, manifest_file, manifest_file_temporary,
                                       k[Storyboard.KEY_ID], k[Storyboard.KEY_TITLE], k[Storyboard.KEY_OVERVIEW],
                                       k[Storyboard.KEY_LEVEL])
                        # Replace start.html by temporary file
                        copy2(start_file_temporary,start_file)
                        os.remove(start_file_temporary)
                        # Replace imsmanifest.xml by temporary file
                        copy2(manifest_file_temporary,manifest_file)
                        os.remove(manifest_file_temporary)

                        # Create name of SCORM package: if path is absolute we use the file name directly,
                        # otherwise we add the program_path prefix
                        if os.path.isabs(scorm_file):
                            package_name = scorm_file
                        else:
                            package_name = program_path + "/" + scorm_file

                        # Create SCORM package
                        if package_name:
                            logging.info("Create SCORM package '{}'.".format(package_name))
                            # TODO: Could use Python zip library to reduce dependency on external packages
                            #       given that zip is not installed by default in CentOS 
                            command = "cd {}; zip -q -r {} *".format(training_name, package_name)
                            logging.debug("Archiving command: {}".format(command))
                            return_value = os.system(command)
                            exit_status = os.WEXITSTATUS(return_value)
                            if exit_status != 0:
                                logging.error("Copy package operation failed.")
                                return False
                        else:
                            logging.error("Package name is not defined.")
                            return False

    except (IOError, yaml.YAMLError) as e:
        logging.error("General error: " + str(e))
        return False

    return True

#############################################################################
# Main program (used for testing purposes)
#############################################################################
def main():

    # Configure logging level for running the tests below
    logging.basicConfig(level=logging.INFO,
                    format='* %(levelname)s: %(filename)s: %(message)s')

    # Setup function arguments
    input_file = "training_example.yml"
    package_file = "training_example.yml.zip"
    ## Get the directory of the program for storing temporary files
    program_path = os.path.dirname(os.path.realpath(__file__))

    # Call the conversion function
    success_status = yaml2scorm(input_file, package_file, program_path)
    if success_status:
        logging.info("SCORM package created successfully for '{}'.".format(input_file))
    else:
        logging.error("Failed to create SCORM package for '{}'.".format(input_file))
        sys.exit(1)

#############################################################################
# Run main program
#############################################################################
if __name__ == "__main__":
    main()

