#!/usr/bin/env python

#############################################################################
# Main file of the CyLMS set of tools for LMS-based cybersecurity training
#############################################################################

# External imports
import logging
import os
import re
import getopt
import sys
import time

# Internal imports
import cfg_mgmt
import cnt2lms
import lms_mgmt
import vnc_mgmt
from storyboard import Storyboard

#############################################################################
# Constants
#############################################################################

# Prefix of files stored in LMS repository; actual file names will be generated
# by appending the current training session id and the extension "zip"
ACTIVITY_NAME_FORMAT = "Activity #{}: {}"
ACTIVITY_DESCRIPTION_FORMAT = "Added on: {}"
LMS_PACKAGE_FILE_FORMAT = "training_content{}.zip"

# Default value of show range button flag
ENABLE_VNC_DEFAULT = False
# Default value of session id to make possible convert operations for testing purposes
SESSION_ID_DEFAULT = "N"

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
    print "                               NOTE: Required for both actions below"
    print "-a, --add-to-lms <SESSION_NO>  Add converted package to LMS using session number"
    print "                               NOTE: Usable only together with 'convert-content'"
    print "-r, --remove-from-lms <NO,ID>  Remove session with given number and activity id"
    print "-v, --vnc-setup <SESSION_NO>   Setup VNC service for accessing the cyber range\n"


#############################################################################
# Main program
#############################################################################
def main(args):

    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='* %(levelname)s: %(filename)s: %(message)s')

    # Program parameters and their default values
    yaml_file = None
    config_file = None
    session_id = None
    activity_id = None

    # Program actions
    convert_action = False
    add_to_lms_action = False
    remove_from_lms_action = False
    vnc_setup_action = False

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
        # Make sure to add ':' for short-form and '=' for long-form options that require an argument
        opts, trailing_args = getopt.getopt(args, "hc:f:a:r:v:",
                                            ["help", "convert-content=", "config-file=",
                                             "add-to-lms=", "remove-from-lms=", "vnc-setup="])
    except getopt.GetoptError as err:
        logging.error("Command-line argument error: {}".format(str(err)))
        usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c", "--convert-content"):
            yaml_file = os.path.abspath(arg)
            convert_action = True
        elif opt in ("-f", "--config-file"):
            config_file = os.path.abspath(arg)
        elif opt in ("-a", "--add-to-lms"):
            session_id = arg
            add_to_lms_action = True
        elif opt in ("-r", "--remove-from-lms"):
            id_list = arg.split(",")
            # Check that split resulted in exactly 2 non-empty strings
            if id_list and len(id_list) == 2 and id_list[0] and id_list[1]:
                session_id = id_list[0]
                activity_id = id_list[1]
                remove_from_lms_action = True
            else:
                logging.error("Action 'remove-from-lms' requires a comma-separated argument (e.g., '1,10'),\n\t"\
                              "but a different format was encountered: '{}'".format(arg))
                usage()
                sys.exit(1)
        elif opt in ("-v", "--vnc-setup"):
            session_id = arg
            vnc_setup_action = True
        else:
            # Nothing to be done on else, since unrecognized options are caught by
            # the getopt.GetoptError exception above
            pass

    if trailing_args:
        logging.error("Unrecognized trailing arguments {} => abort execution.".format(trailing_args))
        usage()
        sys.exit(1)

    # Initialize additional variables
    if config_file:
        cfg_manager = cfg_mgmt.CfgManager(config_file)
    else:
        cfg_manager = None
    scorm_file = None

    # Check that at least one action is enabled
    if not (convert_action or add_to_lms_action or remove_from_lms_action or vnc_setup_action):
        logging.error("No action argument was provided => abort execution.")
        usage()
        sys.exit(1)

    # Check that incompatible actions are not used together
    if convert_action and remove_from_lms_action:
        logging.error("The actions 'convert-content' and 'remove-from-lms' are not compatible => abort execution.")
        usage()
        sys.exit(1)

    # Set show range flag from configuration file or default value
    if cfg_manager:
        if cfg_manager.get_setting(Storyboard.CONFIG_ENABLE_VNC):
            enable_vnc = True
        else:
            enable_vnc = False
        logging.debug("Use configured value of enable_vnc flag: {}".format(enable_vnc))
    else:
        logging.debug("Use default value of enable_vnc flag: {}".format(ENABLE_VNC_DEFAULT))
        enable_vnc = ENABLE_VNC_DEFAULT

    # Proceed with the convert-content action
    if convert_action:
        logging.info("Convert training content file '{}' to SCORM package.".format(yaml_file))
        # Build base name of SCORM package file
        scorm_file_base = yaml_file
        # Convert content to SCORM package
        if not session_id:
            session_id = SESSION_ID_DEFAULT
        scorm_file, training_title = cnt2lms.yaml2scorm(yaml_file, scorm_file_base, dir_path, enable_vnc, session_id, config_file)
        # Check whether the conversion was successful
        if scorm_file:
            logging.debug("Converted training content file '{}' successfully.".format(yaml_file))
        else:
            logging.error("Failed to convert training content file '{}'.".format(yaml_file))
            sys.exit(1)

    # Proceed with the add-to-lms action
    if add_to_lms_action:
        # Check whether the SCORM package name is defined
        if scorm_file:
            logging.info("Add converted SCORM package '{}' to LMS.".format(scorm_file))
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
                        activity_name = ACTIVITY_NAME_FORMAT.format(session_id, training_title.encode('utf-8'))
                        activity_description=ACTIVITY_DESCRIPTION_FORMAT.format(time.strftime("%Y-%m-%d %H:%M:%S"))
                        activity_id = lms_manager.add_activity(activity_name, activity_description, target_file)
                        # Check whether adding the activity was successful
                        if activity_id:
                            # If the value of the activity is needed, it should be parsed
                            # from the program output by the caller
                            logging.info("Added converted SCORM package '{}' to LMS successfully => activity_id={}"
                                          .format(scorm_file, activity_id))
                            # Don't exit to allow chaining with the vnc-setup command
                        else:
                            logging.error("Failed to add converted SCORM package '{}' to LMS.".format(scorm_file))
                            sys.exit(1)
                    else:
                        logging.error("SCORM package copy to LMS repository failed => abort execution.")
                        sys.exit(1)
                else:
                    logging.error("Session id is undefined => abort execution.")
                    usage()
                    sys.exit(1)
            else:
                # Check whether we have an internal error, or the config file was not provided
                if config_file:
                    logging.error("Internal error: Configuration manager is undefined => abort execution.")
                else:
                    logging.error("Configuration file name is undefined => abort execution.\n\t (Note that the 'add-to-lms' action requires the 'config-file' option.)")
                    usage()
                sys.exit(1)
        else:
            logging.error("SCORM package file name is undefined => abort execution.\n\t (Note that the 'add-to-lms' action can only be used together with 'convert-content'.)")
            usage()
            sys.exit(1)

    # Proceed with the remove-from-lms action
    if remove_from_lms_action:
        if session_id and activity_id:
            logging.info("Remove session #{} (activity with id '{}') from LMS.".format(session_id, activity_id))
            if config_file:
                # Create LMS manager object
                lms_manager = lms_mgmt.LmsManager(config_file)
                if lms_manager:
                    # Delete activity with given id
                    package_file = LMS_PACKAGE_FILE_FORMAT.format(session_id)
                    success_status = lms_manager.delete_activity(activity_id, package_file)
                    # Check whether the deletion was successful
                    if success_status:
                        # TODO: Add code to also delete the actual package file from LMS repository?
                        logging.debug("Removed activity with id '{}' from LMS successfully.".format(activity_id))
                    else:
                        logging.error("Failed to remove activity with id '{}' from LMS.".format(activity_id))
                        sys.exit() # Not fatal error anymore, should it be? sys.exit(1)
                else:
                    logging.error("Internal error: LMS manager is undefined => abort execution.")
                    sys.exit(1)

                # If showing the access range button is not enabled return,
                # otherwise stop the noVNC servers
                if not enable_vnc:
                    return

                # Create a VNC manager object
                vnc_manager = vnc_mgmt.VncManager(config_file)
                if vnc_manager:
                    vnc_ports = vnc_manager.get_range_info(session_id)
                    if vnc_ports:
                        if vnc_manager.stop_novnc_servers(session_id, vnc_ports):
                            logging.debug("Stopped VNC servers for session #{} successfully.".format(session_id))
                            sys.exit() # It is OK to exit here as no command chaining is possible
                        else:
                            logging.error("Failed to stop VNC servers => abort VNC server stopping")
                            sys.exit() # Not fatal error anymore, should it be? sys.exit(1)
                    else:
                        logging.error("Failed to get cyber range info => abort VNC server stopping")
                        sys.exit(1)
                else:
                    logging.error("Internal error: VNC manager is undefined => abort execution.")
                    sys.exit(1)
            else:
                logging.error("Configuration file name is undefined => abort execution.\n\t (Note that the 'remove-from-lms' action requires the 'config-file' option.)")
                usage()
                sys.exit(1)

    # Proceed with the vnc-setup action
    if vnc_setup_action:
        if session_id :
            logging.info("Set up VNC server to access the cyber range for session #{}.".format(session_id))
            if config_file:
                # If showing the access range button is not enabled return,
                # otherwise stop the noVNC servers
                if not enable_vnc:
                    logging.info("VNC setup not enabled in the config file => ignore command")
                    return

                # Create a VNC manager object
                vnc_manager = vnc_mgmt.VncManager(config_file)
                if vnc_manager:
                    vnc_ports = vnc_manager.get_range_info(session_id)
                    if vnc_ports:
                        if vnc_manager.create_access_file(session_id, vnc_ports):
                            if vnc_manager.start_novnc_servers(vnc_ports):
                                logging.debug("Started VNC servers for session #{} successfully.".format(session_id))
                                sys.exit()  # It is OK to exit here as no command chaining is possible
                            else:
                                logging.error("Failed to start VNC servers => abort VNC setup")
                                sys.exit(1)
                        else:
                            logging.error("Failed to create range access file => abort VNC setup")
                            sys.exit(1)
                    else:
                        logging.error("Failed to get cyber range info => abort VNC server stopping")
                        sys.exit(1)
                else:
                    logging.error("Internal error: VNC manager is undefined => abort execution.")
                    sys.exit(1)
            else:
                logging.error("Configuration file name is undefined => abort execution.\n\t (Note that the 'remove-from-lms' action requires the 'config-file' option.)")
                usage()
                sys.exit(1)

#############################################################################
# Run program
if __name__ == "__main__":
    main(sys.argv[1:])
