
#############################################################################
# Content to LMS converter for CyLMS
#############################################################################

# External imports
from distutils import dir_util
from distutils.errors import DistutilsFileError
import os
import io
import codecs
import re
import logging
import yaml
import sys
import shutil

# Internal imports
from storyboard import Storyboard
import vnc_mgmt

# Constants
TEMPLATE_DIR = 'Template' # Template SCORM package
REMOVE_TEMP_PKG_DIR = True
YAML2SCORM_ERROR = None, None
DEBUG = False # Use to debug text encoding/conversion issues

#############################################################################
# Functions
# TODO: Use class below instead of just functions?!
#############################################################################


#############################################################################
# Add question to question file in SCORM package
def add_question(question_file, question_file_temp, question_id, question_body,
                 question_type, question_answer, question_correct_answer, question_hints):

    # Define objective ID of training (by default is obj_playing, do not change it)
    question_objective_id = """obj_playing"""

    if question_type == Storyboard.VALUE_TYPE_FILL_IN: question_type = 'QUESTION_TYPE_FILL'
    elif question_type == Storyboard.VALUE_TYPE_NUMERIC: question_type = 'QUESTION_TYPE_NUMERIC'
    elif question_type == Storyboard.VALUE_TYPE_CHOICE: question_type = 'QUESTION_TYPE_CHOICE'

    hints = []
    if question_hints:
        for hint in question_hints:
            # Need to check type both for string and unicode (for JA support)
            if type(hint) == str or type(hint) == unicode:
                logging.debug("Question hint: " + repr(hint))
                hints.append(hint)
            else:
                logging.error("Incorrect format for hint string: " + repr(hint).decode("unicode-escape"))
                return False
    else:
        # If the value is None, it means the 'hints' tag was used, so we return error;
        # otherwise the value is an empty string, meaning the 'hints' tag was not used,
        # hence we do nohing
        if question_hints is None:
            logging.error("No strings provided in the 'hints' array.")
            return False

    my_f = io.open(question_file,'r',encoding='utf8')
    temp = io.open(question_file_temp,'ab')

    # Replace content in template file
    content = my_f.read().encode('utf-8')
    # Convert int to unicode
    temp_list = [question_id, question_body, question_type, question_answer, question_correct_answer, question_objective_id]
    for counter, i in enumerate(temp_list):
        if isinstance(i, int): 
            temp_list[counter] = str(i).encode('utf-8') 
    question_id, question_body, question_type, question_answer, question_correct_answer, question_objective_id = temp_list

    # Pre-processing of question fields
    # Change symbol " to \" to avoid errors in HTML, then avoid the case \\
    # Output goes to 'Playing/questions.js'
    if DEBUG: print "---------------------------------------------------------"
    ## Process question id
    if DEBUG: print "- Question id: ORIGINAL: " + question_id
    question_id = question_id.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    if DEBUG: print "  Question id: ENCODED : " + question_id
    ## Process question body
    if DEBUG: print "- Question body: ORIGINAL: " + question_body
    question_body = question_body.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    if DEBUG: print "  Question body: ENCODED : " + question_body
    ## Process question type
    question_type = question_type.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    ## Process question answer
    if DEBUG: print "- Question answer: ORIGINAL: " + question_correct_answer
    question_correct_answer = question_correct_answer.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    if DEBUG: print "  Question answer: ENCODED : " + question_correct_answer
    ## Process choices for multiple-choice questions
    if DEBUG: print "- Question choices: ORIGINAL: " + str(question_answer)
    ### Create choice data appropriate for inclusion in JavaScript file
    choice_data = build_choice_data(question_answer)
    if DEBUG: print "  Question choices: ENCODED: " + choice_data
    ## ObjectiveId is predefined as 'obj_playing' and should not be changed (see above), so do nothing
    #question_objective_id = question_objective_id.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    ## Process hints
    for i in range(0,len(hints)):
        if DEBUG: print "- Hint #" + str(i+1) +": ORIGINAL: " + hints[i]
        hints[i] = hints[i].encode('utf-8').replace('"','\\"').replace('\\\\','\\')
        if DEBUG: print "  Hint #" + str(i+1) +": ENCODED : " + hints[i]

    # Insert information into the overall 'content' object
    ## Add question id
    content = content.replace(Storyboard.TAG_QUESTION_ID, str(question_id))
    ## Add question body
    content = content.replace(Storyboard.TAG_QUESTION_BODY, str(question_body))
    ## Add question type
    content = content.replace(Storyboard.TAG_QUESTION_TYPE, str(question_type))
    ## Add question answer
    content = content.replace(Storyboard.TAG_QUESTION_CORRECT_ANSWER, str(question_correct_answer))
    ## Add choices for multiple-choice questions
    ### This a special case for which we need to put the choices in an array
    if question_type == 'QUESTION_TYPE_CHOICE':
        content = content.replace(Storyboard.TAG_QUESTION_ANSWER, 'new Array({})'.format(Storyboard.TAG_QUESTION_ANSWER))
    content = content.replace(Storyboard.TAG_QUESTION_ANSWER, str(choice_data))
    ## TODO: Add what?
    content = content.replace(Storyboard.TAG_QUESTION_OBJECTIVE_ID, str(question_objective_id))
    ## Add hints individually
    for i in range(0,len(hints)):
        content = content.replace(Storyboard.TAG_QUESTION_HINT + str(i+1), hints[i])
    content = re.sub('".*{}.*"'.format(Storyboard.TAG_QUESTION_HINT),'""',content)

    logging.debug("Content: "+content)
    temp.write(content)
    my_f.close()
    temp.close()

    return True


#############################################################################
# Build choice data appropriate for inclusion in JavaScript file
def build_choice_data(question_choices):

    # Initialize to default value for fill-in questions
    choice_data = "null"

    # Deal with options for multiple-choice questions
    if question_choices != "null":

        # Initialize processed option list
        option_list2 = []

        # If input is not a list, we assume it's a string that we must split by the ',' character
        if not type(question_choices) is list:

            # Split options by comma
            option_list = question_choices.split(",")
        else:
            # No need to split, just copy the input
            option_list = question_choices

        # Process options
        for option in option_list:

            # Remove white spaces at beginning and end of string
            option = option.strip()

            # Later we enclose option in double quotes, so we must strip the
            # first and last double quote characters (if they exist);
            # we also do some basic consistency checking just in case
            if option.startswith('"'):
                option = option[1:]
                if option.endswith('"'):
                    option = option[:-1]
                else:
                    logging.error("Incorrect use of double quote symbols for option: " + option)
                    return None
            elif option.endswith('"'):
                logging.error("Incorrect use of double quote symbols for option: " + option)
                return None

            # Any other double quote characters must be escaped
            # TODO: we also remove escape for backslash to match similar
            # code in add_question() function above, but is it needed?
            option = option.replace('"', '\\"').replace('\\\\','\\')

            # Add double quote prefix and suffix for JavaScript string
            option = '"' + option + '"'

            # Append option to processed option list
            option_list2.append(option)

        # Build choice data string appropriate for JavaScript
        choice_data = ""
        for option in option_list2:
            choice_data += (option.encode('utf-8') + ", ")

        # Remove the last unnecessary comma and space
        choice_data=choice_data[:-2]

    logging.debug("build_choice_data: choice_data='" + choice_data + "'")

    return choice_data


#############################################################################
# Add information not related to questions to auxiliary SCORM package files
def add_information(start_file, start_file_temp, manifest_file,
                    manifest_file_temp, id, enable_vnc,
                    description, header, level, session_id, config_file):

    # Write description information to template manifest_file
    file = io.open(manifest_file,'r')
    temp = io.open(manifest_file_temp,'ab')

    content = file.read()
    idText = str(id)
    content = content.replace(Storyboard.TAG_TRAINING_ID, idText.encode('utf-8'))

    logging.debug("Content: " + content)
    temp.write(content)
    file.close()
    temp.close()

    # Write description information to template start_file
    file = io.open(start_file,'r')
    temp = io.open(start_file_temp,'ab')

    # Get file content
    content = file.read().encode('utf-8')
    # Build the level text
    if level:
        level_text = "Level {0}: ".format(str(level).encode('utf-8'))
    else:
        level_text = ""

    # Replace special tags with actual content
    # Output goes to 'shared/assessmenttemplate.html'
    if DEBUG: print "---------------------------------------------------------"
    ## Show range button tag is predefined, so no encoding needed
    ## NOTE: We show the range button in SCORM if VNC access is enabled
    content = content.replace(Storyboard.TAG_SHOW_RANGE_BUTTON, str(enable_vnc).lower())
    ## Training level is just a number, so no encoded needed
    content = content.replace(Storyboard.TAG_TRAINING_LEVEL, level_text)
    ## Training title
    if DEBUG: print("- Training title: ORIGINAL: '{}'".format(description))
    training_title = description.encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    if DEBUG: print("- Training title: ENCODED : '{}'".format(training_title))
    content = content.replace(Storyboard.TAG_TRAINING_TITLE, training_title)
    ## Training overview: need to strip trailing white spaces to make a correct HTML file
    if DEBUG: print("- Training overview: ORIGINAL: '{}'".format(header))
    training_overview = header.rstrip().encode('utf-8').replace('"','\\"').replace('\\\\','\\')
    training_overview = '<br>'.join(training_overview.splitlines())
    if DEBUG: print("- Training overview: ENCODED : '{}'".format(training_overview))
    content = content.replace(Storyboard.TAG_TRAINING_OVERVIEW, training_overview)
    ## Range access information
    ### Set a default value first
    port_filename = ":{}/access_range{}.html".format(Storyboard.ACCESS_RANGE_BASE_PORT, session_id)
    ### Try to determine correct info
    if enable_vnc and session_id.isdigit():
        # Create a VNC manager object
        vnc_manager = vnc_mgmt.VncManager(config_file)
        if vnc_manager:
            vnc_ports = vnc_manager.get_range_info(session_id)
            if vnc_ports:
                first_access_range_port = vnc_ports[0] - Storyboard.VNC_BASE_PORT + Storyboard.ACCESS_RANGE_BASE_PORT
                port_filename = ":{}/access_range{}.html".format(first_access_range_port, session_id)
            else:
                logging.error("Failed to get cyber range info => abort VNC server stopping")
    if DEBUG: print("- Port & file name: '{}'".format(port_filename))
    content = content.replace(Storyboard.TAG_PORT_FILENAME, port_filename)
    if DEBUG: print "---------------------------------------------------------"

    logging.debug("Content: " + content)
    temp.write(content)
    file.close()
    temp.close()


#########################################################################
# Convert training content description in YAML format to a SCORM package;
# if absolute path is not provided, the SCORM file is saved in the program path
# NOTE: Currently this function only supports YAML files with one question set
def yaml2scorm(input_file, scorm_file, program_path, enable_vnc, session_id, config_file):

    # Check whether input file was provided
    if input_file:
        logging.info("Process training content file '{}'.".format(input_file))
    else:
        logging.error("Training content file invalid: {}.".format(input_file))
        return YAML2SCORM_ERROR

    # Build sets with valid keys for training and question sections
    valid_training_keys = set([Storyboard.KEY_ID, Storyboard.KEY_TITLE, Storyboard.KEY_RESOURCES,
                               Storyboard.KEY_OVERVIEW, Storyboard.KEY_LEVEL, Storyboard.KEY_QUESTIONS])
    valid_question_keys = set([Storyboard.KEY_ID, Storyboard.KEY_TYPE, Storyboard.KEY_BODY,
                               Storyboard.KEY_CHOICES, Storyboard.KEY_ANSWER, Storyboard.KEY_HINTS])

    try:
        with codecs.open(input_file, 'r', 'utf-8') as stream:
            yaml_stream = yaml.load(stream)
            logging.debug("YAML stream: " + str(yaml_stream))
            if not yaml_stream:
                logging.error("No data in the input file: " + input_file)
                return YAML2SCORM_ERROR
            for top_object in yaml_stream:
                if type(top_object) != dict:
                    logging.error("Incorrect format in the input file: " + input_file)
                    return YAML2SCORM_ERROR
                for yaml_tag in top_object:
                    # Check that top-level tag matches 'training'
                    if yaml_tag != Storyboard.KEY_TRAINING:
                        logging.error("Top-level section in training content does not match '{0}': {1}".format(Storyboard.KEY_TRAINING, yaml_tag))
                        return YAML2SCORM_ERROR

                    # Process tags within training section
                    for training in top_object[yaml_tag]:

                        # Check whether any unknown tags are present
                        training_keys = set(training.keys())
                        unknown_training_keys = training_keys.difference(valid_training_keys)
                        if unknown_training_keys:
                            logging.error("Unknown tags found in training content: " + repr(list(unknown_training_keys)))
                            return YAML2SCORM_ERROR

                        # Check existence of required fields in training section
                        if Storyboard.KEY_ID not in training:
                            logging.error("Required field in training content is missing: " + Storyboard.KEY_ID)
                            return YAML2SCORM_ERROR
                        if Storyboard.KEY_TITLE not in training:
                            # Use id as title if title is not provided (we know that id must be defined at
                            # this point, as we have checked it in the previous if statement)
                            training[Storyboard.KEY_TITLE] = training[Storyboard.KEY_ID]
                        if Storyboard.KEY_OVERVIEW not in training:
                            logging.error("Required field in training content is missing: " + Storyboard.KEY_OVERVIEW)
                            return YAML2SCORM_ERROR
                        # Although questions are in principle not optional, we allow content descriptions without
                        # questions in order to have more flexibility (e.g., to generate default content)
                        #if Storyboard.KEY_QUESTIONS not in training:
                        #    logging.error("Required field in training content is missing: " + Storyboard.KEY_QUESTIONS)
                        #    return YAML2SCORM_ERROR

                        # If optional field 'level' is not found in the input file, we provide 
                        # a default value for it
                        if Storyboard.KEY_LEVEL not in training:
                            training[Storyboard.KEY_LEVEL] = None

                        # Define training name and make new package folder for new SCORM package
                        training_name = training[Storyboard.KEY_ID]

                        # Change the training name to the full path directory:
                        training_name = str(program_path) + "/" + str(training_name)

                        # Get the resources directory if defined
                        if Storyboard.KEY_RESOURCES in training:
                            resources = training[Storyboard.KEY_RESOURCES]
                            # Build the absolute path for the resources directory
                            resources = os.path.abspath(resources)
                        else:
                            resources = None

                        # Copy from the template package to the new package
                        try:
                            dir_util.copy_tree(str(program_path) + "/" + TEMPLATE_DIR, training_name)
                            # If defined, copy the content of the resources directory
                            # into the 'shared' folder inside the SCORM package
                            if resources:
                                dir_util.copy_tree(resources, training_name + "/shared")
                        except DistutilsFileError as e:
                            logging.error("Issue when copying template: " + str(e))
                            return YAML2SCORM_ERROR

                        # Add questions to temporary file
                        # Workflow: get template from question.js, fill in the content for each question and
                        # add one by one question into temporary file. After finish, replace question.js by
                        # the temporary file and delete the temporary one.
                        question_file = training_name + '/Playing/questions.js'
                        question_file_temp = question_file + '_temp'

                        # Process questions
                        if Storyboard.KEY_QUESTIONS in training:
                            for question in training[Storyboard.KEY_QUESTIONS]:

                                # Check whether any unknown tags are present
                                question_keys = set(question.keys())
                                unknown_question_keys = question_keys.difference(valid_question_keys)
                                if unknown_question_keys:
                                    logging.error("Unknown tags found in question section: " + repr(unknown_question_keys))
                                    return YAML2SCORM_ERROR

                                # Check existence of required fields in question section
                                if Storyboard.KEY_ID not in question:
                                    logging.error("Required field in question section is missing: " + Storyboard.KEY_ID)
                                    return YAML2SCORM_ERROR
                                if Storyboard.KEY_BODY not in question:
                                    logging.error("Required field in question '{0}' section is missing: {1}"
                                                  .format(question[Storyboard.KEY_ID], Storyboard.KEY_BODY))
                                    return YAML2SCORM_ERROR
                                if Storyboard.KEY_ANSWER not in question:
                                    logging.error("Required field in question '{0}' section is missing: {1}"
                                                  .format(question[Storyboard.KEY_ID], Storyboard.KEY_ANSWER))
                                    return YAML2SCORM_ERROR

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
                                    return YAML2SCORM_ERROR
                                if question[Storyboard.KEY_TYPE] == Storyboard.VALUE_TYPE_CHOICE and Storyboard.KEY_CHOICES not in question:
                                    logging.error("Fill-in type questions must have a '{0}' field.".format(Storyboard.KEY_CHOICES))
                                    return YAML2SCORM_ERROR

                                # If a question has no 'choices' field, then we set it to 'null' 
                                # so that it is dealt with appropriately in JavaScript
                                if Storyboard.KEY_CHOICES not in question:
                                    question[Storyboard.KEY_CHOICES] = "null"

                                # If optional field 'hints' is not provided, we set it to ''
                                if Storyboard.KEY_HINTS not in question:
                                    question[Storyboard.KEY_HINTS] = ""

                                # Actually add the question to the internal data structure
                                add_question(question_file, question_file_temp, question[Storyboard.KEY_ID],
                                             question[Storyboard.KEY_BODY], question[Storyboard.KEY_TYPE],
                                             question[Storyboard.KEY_CHOICES], question[Storyboard.KEY_ANSWER],
                                             question[Storyboard.KEY_HINTS])

                            # Only copy the temporary question file if there were some questions to start with
                            # Replace question.js by temporary file
                            shutil.copy2(question_file_temp, question_file)
                            os.remove(question_file_temp)

                        # Add information about level, header and description
                        start_file = training_name + '/shared/assessmenttemplate.html'
                        start_file_temp = start_file + '_temp'
                        manifest_file = training_name + '/imsmanifest.xml'
                        manifest_file_temp = manifest_file + '_temp'

                        add_information(start_file, start_file_temp, manifest_file, manifest_file_temp,
                                        training[Storyboard.KEY_ID], enable_vnc, training[Storyboard.KEY_TITLE],
                                        training[Storyboard.KEY_OVERVIEW], training[Storyboard.KEY_LEVEL], session_id, config_file)
                        # Replace start.html by temporary file
                        shutil.copy2(start_file_temp, start_file)
                        os.remove(start_file_temp)
                        # Replace imsmanifest.xml by temporary file
                        shutil.copy2(manifest_file_temp, manifest_file)
                        os.remove(manifest_file_temp)

                        # Create name of SCORM package: if path is absolute we use the file name directly,
                        # otherwise we add the program_path prefix
                        if os.path.isabs(scorm_file):
                            base_package_name = scorm_file
                        else:
                            base_package_name = program_path + "/" + scorm_file

                        # Create SCORM package
                        package_name = shutil.make_archive(base_package_name, "zip", training_name)
                        if REMOVE_TEMP_PKG_DIR:
                            shutil.rmtree(training_name)
                        if package_name:
                            logging.info("Created SCORM package '{}'.".format(package_name))
                            return package_name, training[Storyboard.KEY_TITLE]
                        else:
                            logging.error("Package creation failed.")
                            return YAML2SCORM_ERROR

    except (IOError, yaml.YAMLError) as e:
        logging.error("General error: " + str(e))
        return YAML2SCORM_ERROR


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
    enable_vnc = False
    session_id = "N"
    config_file = "config_example"
    success_status = yaml2scorm(input_file, package_file, program_path, enable_vnc, session_id, config_file)
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

