#!/usr/bin/python

#############################################################################
# Main file of the CyLMS set of tools for LMS-based cybersecurity training
#############################################################################

# External imports
import logging
import os
import re
import getopt
import sys

# Internal imports
import cfg_mgmt
import lms_mgmt
import cnt2lms


#############################################################################
# Constants
#############################################################################

# Prefix of files stored in LMS repository; actual file names will be generated
# by appending the current training session id and the extension "zip"
ACTIVITY_NAME_FORMAT = "Training Session #{}"
LMS_PACKAGE_FILE_FORMAT = "training_content{}.zip"

#############################################################################
# Functions
#############################################################################

# Print usage information
def usage():
    print "\nOVERVIEW: CyLMS set of tools for cybersecurity training support in Learning Management Systems (LMS).\n"
    print "USAGE: cylms.py [options]\n"
    print "OPTIONS:"
    print "-h, --help                     Display this help message and exit"
    print "-c, --convert-content <FILE>   Convert training content file to SCORM package"
    print "-f, --config-file <CONFIG>     Set configuration file for LMS integration tasks"
    print "                               NOTE: Required for all the operations below"
    print "-a, --add-to-lms <SESSION_NO>  Add converted package to LMS using session number"
    print "                               NOTE: Usable only together with 'convert-content'"
    print "-r, --remove-from-lms <NO,ID>  Remove session with given number and activity id\n"


#############################################################################
# Main program
#############################################################################
def main(argv):

    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='* %(levelname)s: %(filename)s: %(message)s')

    # Program parameters and their default values
    yaml_file = None
    scorm_file = None
    config_file = None
    session_id = None
    activity_id = None

    # Program actions
    convert_action = False
    add_to_lms_action = False
    remove_from_lms_action = False

    # Get program directory
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Print banner (read version from CHANGES file)
    version_string = 'CyLMS'
    changes_filename = str(dir_path) + "/CHANGES"
    try:
        changes_file = open(changes_filename)
        for line in changes_file:
            if re.match("CyLMS v", line):
                version_string = line.rstrip()
                break
    except IOError:
        # In case file cannot be opened/read, we use the default value
        pass        
    print("#########################################################################")
    print("{}: Cybersecurity Training Support for LMS".format(version_string))
    print("#########################################################################")

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(argv, "hc:f:a:r:", ["help", "convert=", "config-file=", "add-to-lms=", "remove-from-lms"])
    except getopt.GetoptError as err:
        logging.error("Command-line argument error: {}".format(str(err)))
        usage()
        quit(-1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            quit()
        elif opt in ("-c", "--convert"):
            yaml_file = os.path.abspath(arg)
            convert_action = True
        elif opt in ("-f", "--config"):
            config_file = os.path.abspath(arg)
            cfg_manager = cfg_mgmt.CfgManager(config_file)
        elif opt in ("-a", "--add-to-lms"):
            session_id = arg
            add_to_lms_action = True
        elif opt in ("-r", "--'remove-from-lms"):
            id_list = arg.split(",")
            # Check that split resulted in exactly 2 non-empty strings
            if id_list and len(id_list) == 2 and id_list[0] and id_list[1]:
                session_id = id_list[0]
                activity_id = id_list[1]
                remove_from_lms_action = True
            else:
                logging.error("Operation remove-from-lms requires a comma-separated argument (e.g., '1,10'),\n\t"\
                              "but a different format was encountered: '{}'".format(arg))
                usage()
                quit(-1)

    # Check that at least one action is enabled
    if not (convert_action or add_to_lms_action or remove_from_lms_action):
        logging.error("No action argument was provided => abort execution.")
        usage()
        quit(-1)
        
    # Proceed with the convert-content action
    if convert_action:
        logging.info("Convert training content file '{}' to SCORM package.".format(yaml_file))
        # Build name of SCORM package file
        scorm_file = yaml_file+".zip"
        # Convert content to SCORM package
        success_status = cnt2lms.yaml2scorm(yaml_file, scorm_file, dir_path)
        # Check whether the conversion was successful
        if success_status:
            logging.debug("Converted training content file '{}' successfully.".format(yaml_file))
        else:
            logging.error("Failed to convert training content file '{}'.".format(yaml_file))
            quit(-1)

    # Proceed with the add-to-lms action
    if add_to_lms_action:
        logging.info("Add converted SCORM package '{}' to LMS.".format(scorm_file))
        # Check whether the SCORM package name is defined
        if scorm_file:
            # Check whether the configuration manager is defined
            if cfg_manager:
                # Check whether the session id (number) is defined
                if session_id:
                    # Create LMS manager object
                    lms_manager = lms_mgmt.LmsManager(config_file)
                    # Build target package name and copy local SCORM package to repository
                    target_file = LMS_PACKAGE_FILE_FORMAT.format(session_id)
                    success_status = lms_manager.copy_package(scorm_file, target_file)

                    # Check whether copy package operation was successful
                    if success_status:
                        # If copy was successful, we add a corresponding activity to LMS
                        activity_name = ACTIVITY_NAME_FORMAT.format(session_id)
                        activity_id = lms_manager.add_activity(activity_name, target_file)
                        # Check whether adding the activity was successful
                        if activity_id:
                            logging.debug("Added converted SCORM package '{}' to LMS successfully.".format(scorm_file))
                            # We return the id as execution status (positive value means success)
                            quit(activity_id)
                        else:
                            logging.error("Failed to add converted SCORM package '{}' to LMS.".format(scorm_file))
                            quit(-1)
                    else:
                        logging.error("SCORM package copy to LMS repository failed => abort execution.")
                        quit(-1)
                else:
                    logging.error("Session id is undefined => abort execution.")
                    usage()
                    quit(-1)
            else:
                logging.error("Configuration manager is undefined => abort execution.")
                usage()
                quit(-1)
        else:
            logging.error("SCORM package file name is undefined => abort execution.\n\t (Note that the 'add-to-lms' action can only be used together with 'convert-content')")
            usage()
            quit(-1)

    # Proceed with the remove-from-lms action
    if remove_from_lms_action:
        logging.info("Remove session #{} (activity with id '{}') from LMS.".format(session_id, activity_id))
        # Create LMS manager object
        lms_manager = lms_mgmt.LmsManager(config_file)
        # Delete activity with given id
        package_file = LMS_PACKAGE_FILE_FORMAT.format(session_id)
        success_status = lms_manager.delete_activity(activity_id, package_file)
        # Check whether the deletion was successful
        if success_status:
            # TODO: Add code to also delete the actual package file from LMS repository?@
            logging.debug("Removed activity with id '{}' from LMS successfully.".format(activity_id))
        else:
            logging.error("Failed to remove activity with id '{}' from LMS.".format(activity_id))
            quit(-1)

#############################################################################
# Run program
if __name__ == "__main__":
    main(sys.argv[1:])
