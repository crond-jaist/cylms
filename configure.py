#!/usr/bin/env python

#############################################################################
# Configuration wizard for CyLMS
#############################################################################

# External imports
import logging
import subprocess
import sys
import ConfigParser
import os

# Internal imports
from storyboard import Storyboard

#############################################################################
# Constants
#############################################################################

#############################################################################
# Constants regarding dependency check

# Command to check whether pip is installed, and to install it (on Ubuntu)
PIP_CHECK_CMD = ["which", "pip"]
PIP_INSTALL_CMD = ["sudo", "apt", "install", "python-pip"]

# Dictionary of required modules and their package names
REQUIRED_PKGS = {"yaml": "PyYAML"}
PKG_INSTALL_CMD = ["sudo", "-H", "pip", "install"]
PROXY_OPTION = "--proxy="
PROXY_OPTION_INDEX = 3 # Insert after pip command

#############################################################################
# Constants regarding SCORM template

# Name of the Moodle VM files: XML definition and QCOW2 disk image
MOODLE_XML = "moodle.xml"
MOODLE_QCOW2 = "moodle.qcow2"
VIRSH_DEFINE_CMD = ["virsh",  "define"]
VIRSH_START_CMD = ["virsh",  "start", "moodle"]
SOURCE_TAG = "<source"
FILE_TAG = "file="

#############################################################################
# Constants regarding SCORM template

# Name of the SCORM template creation script
TEMPLATE_SCRIPT = "create_scorm_template.sh"

#############################################################################
# Constants regarding configuration file

DEFAULT_FILENAME = "config_file"
DEFAULT_LMS_HOST = "root@192.168.122.232"
DEFAULT_LMS_REPOSITORY = "/var/moodledata/repository/training_content/"
DEFAULT_COURSE_NAME = "CyTrONE Training"
DEFAULT_SECTION_ID = "0"
DEFAULT_ENABLE_VNC = "true"
DEFAULT_RANGE_DIRECTORY = "/home/cyuser/cyris/cyber_range"

#############################################################################
# Constants regarding usage examples

DEFAULT_TRAINING_FILE = "training_example.yml"
DEFAULT_SESSION_NO = 1


#############################################################################
# Configuration functions
# NOTE: References below are to CyLMS User Guide from May 2018
#############################################################################

#############################################################################
# Check dependencies for CyLMS
# Reference: Section 3.2.1 "Software requirements"
def check_dependencies(step_no, proxy_server):

    print("\n* STEP {}: Checking dependencies...".format(step_no))

    # Check that pip is installed
    print("  - Check that Python package manager 'pip' is installed")
    try:
        cmd_output = subprocess.check_output(PIP_CHECK_CMD, stderr=subprocess.STDOUT)
        logging.debug("Command output: {}".format(cmd_output.rstrip()))
    except subprocess.CalledProcessError as error:
        print("    + Package manager 'pip' not present => installing (assume Ubuntu OS)...")

        try:
            # NOTE: As there seems to be no way to specify a proxy on command-line for apt,
            # we rely here on the system-wide or /etc/apt/apt.conf proxy setting (if any)
            # TODO: Could use environment setting as for create_scorm_template.sh, but if apt
            # doesn't work, the system is not properly configured anyway
            cmd_output = subprocess.check_output(PIP_INSTALL_CMD, stderr=subprocess.STDOUT)
            logging.debug("Command output: {}".format(cmd_output.rstrip()))
        except subprocess.CalledProcessError as error:
            logging.error("Failed to install 'pip' (proxy or OS issue?!); please do it manually before proceeding.")
            sys.exit(1)
        print("      > DONE: 'pip' was installed successfully")

    # Check that required modules are installed
    success = True
    for module in REQUIRED_PKGS:
        try:
            print("  - Check that Python module '{}' is installed".format(module))
            __import__(module)
        except ImportError:
            print("    + Module '{}' not present => installing package '{}'...".format(module, REQUIRED_PKGS[module]))
            cmd = PKG_INSTALL_CMD
            # If we use a proxy server, the appropriate option needs to be
            # inserted into the pip command
            if proxy_server:
                cmd[PROXY_OPTION_INDEX:PROXY_OPTION_INDEX] = [PROXY_OPTION + proxy_server]
            cmd.append(REQUIRED_PKGS[module])
            logging.debug("Command: " + str(cmd))
            try:
                cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as error:
                logging.error("Could not install module via the 'pip' command.")
                #Error message: {}".format(error.output))
                success = False
                break
            print("      > DONE: '{}' was installed successfully".format(module))

    # Status notification
    if success:
        print("  STEP {}: Dependency check completed successfully".format(step_no))
    else:
        print("  FAILED: Dependency check failed => abort execution")
        print("  NOTE: In case you are using a proxy server, you may need to provide it")
        print("        as argument: $ ./configure.py http://PROXY_IP:PROXY_PORT")
        sys.exit(1)


#############################################################################
# Create SCORM template
# Reference: Section 3.2.2 "Program setup", item 3
def create_template(step_no, proxy_server):
    print("\n* STEP {}: Creating the SCORM template...".format(step_no))

    cylms_path_detected = os.path.dirname(os.path.realpath(__file__))

    # CyLMS path
    cylms_path = raw_input("  - Enter the CyLMS installation path (detected '{}'): ".format(cylms_path_detected))
    if not cylms_path:
        cylms_path = cylms_path_detected
    logging.debug("{} = {}".format("CyLMS path", cylms_path))

    # Template directory
    template_path = raw_input("  - Enter the SCORM template creation script path (default is '{}'): ".format(cylms_path_detected))
    if not template_path:
        template_path = cylms_path_detected
    template_script = template_path + "/" + TEMPLATE_SCRIPT
    logging.debug("{} = {}".format("SCORM script", template_script))

    if not os.path.isfile(template_script):
        logging.error("SCORM template creation script '{}' not found.".format(template_script))
        logging.error("Please make sure that the file exists before proceeding.")
        sys.exit(1)

    # Run command to generate template
    if proxy_server:
        proxy_environment = {"http_proxy": proxy_server}
    else:
        proxy_environment = None

    template_cmd = ["sh", template_script, cylms_path]
    logging.debug("Command: " + str(template_cmd))
    print("  - Installing SCORM template into '{}/Template'...".format(cylms_path))
    try:
        template_cmd_output = subprocess.check_output(template_cmd, env=proxy_environment, stderr=subprocess.STDOUT)
        #print(template_cmd_output)
    except subprocess.CalledProcessError as error:
        logging.error("Execution of the SCORM template creation script '{}' failed.".format(template_script))
        logging.error("Please make sure that the CyLMS path is correct, and Internet access is available.")
        logging.error("Error message: {}".format(error.output))
        sys.exit(1)

    print("  STEP {}: SCORM template created successfully".format(step_no))


#############################################################################
# Generate configuration file for CyLMS
# Reference: Section 3.2.3 "Configuration file"
def generate_config(step_no):
    print("\n* STEP {}: Generating the configuration file...".format(step_no))

    config = ConfigParser.SafeConfigParser()
    config.add_section(Storyboard.CONFIG_SECTION)

    # Get lms_host
    value = raw_input("  - Enter the host name or IP of the LMS host (default is '{}'): ".format(DEFAULT_LMS_HOST))
    if not value:
        value = DEFAULT_LMS_HOST
    logging.debug("{} = {}".format(Storyboard.CONFIG_LMS_HOST, value))
    config.set(Storyboard.CONFIG_SECTION, Storyboard.CONFIG_LMS_HOST, value)

    # Get lms_repository
    value = raw_input("  - Enter the LMS repository (default is '{}'): ".format(DEFAULT_LMS_REPOSITORY))
    if not value:
        value = DEFAULT_LMS_REPOSITORY
    logging.debug("{} = {}".format(Storyboard.CONFIG_LMS_REPOSITORY, value))
    config.set(Storyboard.CONFIG_SECTION, Storyboard.CONFIG_LMS_REPOSITORY, value)

    # Get course_name
    value = raw_input("  - Enter the LMS course name for uploaded activities (default is '{}'): ".format(DEFAULT_COURSE_NAME))
    if not value:
        value = DEFAULT_COURSE_NAME
    logging.debug("{} = {}".format(Storyboard.CONFIG_COURSE_NAME, value))
    config.set(Storyboard.CONFIG_SECTION, Storyboard.CONFIG_COURSE_NAME, value)

    # Get section_id
    value = raw_input("  - Enter the LMS section id for uploaded activities (default is '{}'): ".format(DEFAULT_SECTION_ID))
    if not value:
        value = DEFAULT_SECTION_ID
    logging.debug("{} = {}".format(Storyboard.CONFIG_SECTION_ID, value))
    config.set(Storyboard.CONFIG_SECTION, Storyboard.CONFIG_SECTION_ID, value)

    # Get enable_vnc
    value = raw_input("  - Enable cyber range access via VNC (default is '{}'): ".format(DEFAULT_ENABLE_VNC))
    if not value:
        value = DEFAULT_ENABLE_VNC
    logging.debug("{} = {}".format(Storyboard.CONFIG_ENABLE_VNC, value))
    config.set(Storyboard.CONFIG_SECTION, Storyboard.CONFIG_ENABLE_VNC, value)

    # Get range_directory
    value = raw_input("  - Enter the cyber range directory (default is '{}'): ".format(DEFAULT_RANGE_DIRECTORY))
    if not value:
        value = DEFAULT_RANGE_DIRECTORY
    logging.debug("{} = {}".format(Storyboard.CONFIG_RANGE_DIRECTORY, value))
    config.set(Storyboard.CONFIG_SECTION, Storyboard.CONFIG_RANGE_DIRECTORY, value)

    # Get configuration file name
    value = raw_input("  - Ready to save configuration file => enter its name (default is '{}'): ".format(DEFAULT_FILENAME))
    if not value:
        value = DEFAULT_FILENAME
    logging.debug("Configuration file = {}".format(value))
    config_filename = value

    # Write the configuration file to disk
    with open(config_filename, "w") as config_file:
        config.write(config_file)

    print("  STEP {}: Configuration saved successfully to file '{}'".format(step_no, config_filename))

    return config_filename


#############################################################################
# Set up the Moodle VM
# Reference: Section 3.1.1 "Moodle VM setup"
def setup_moodle(step_no):
    print("\n* STEP {}: Setting up the Moodle VM...".format(step_no))

    # Determine CyLMS path
    cylms_path_detected = os.path.dirname(os.path.realpath(__file__))

    # Get path for Moodle VM files
    moodle_path = raw_input("  - Enter the Moodle VM definition and disk image file path (default is '{}'): ".format(cylms_path_detected))
    if not moodle_path:
        moodle_path = cylms_path_detected

    # Build names of the Moodle VM files (XML and QCOW2)
    xml_file = moodle_path + "/" + MOODLE_XML
    logging.debug("{} = {}".format("Moodle XML file", xml_file))
    qcow2_file = moodle_path + "/" + MOODLE_QCOW2
    logging.debug("{} = {}".format("Moodle QCOW2 file", qcow2_file))

    # Check that the Moodle VM files exist
    if os.path.isfile(xml_file):
        print("    + Found Moodle VM definition file: {}".format(xml_file))
    else:
        logging.error("Moodle VM definition file '{}' not found.".format(xml_file))
        logging.error("Please make sure that the file exists before proceeding.")
        sys.exit(1)
    if os.path.isfile(qcow2_file): 
        print("    + Found Moodle VM disk image file: {}".format(qcow2_file))
    else:
        logging.error("Moodle VM disk image file '{}' not found.".format(qcow2_file))
        logging.error("Please make sure that the file exists before proceeding.")
        sys.exit(1)

    # Update disk image path in VM definition file
    print("  - Updating the disk image path in the Moodle VM definition file...")
    ## First read entire file
    with open(xml_file, "r") as xml_content:
        lines = xml_content.readlines()
    ## Then search for the line containing the source and file tags and update it
    with open(xml_file, "w") as xml_content:
        for line in lines:
            if SOURCE_TAG in line and FILE_TAG in line:
                logging.debug("Original line: {}".format(line.rstrip()))
                tag_start = line.find(FILE_TAG)
                updated_line = line[:tag_start]+FILE_TAG+"'"+qcow2_file+"'/>\n"
                logging.debug("Updated line: {}".format(updated_line.rstrip()))
                xml_content.write(updated_line)
            else:
                xml_content.write(line)

    # Run command to define VM
    # TODO: Check that virsh is available!!!
    VIRSH_DEFINE_CMD.append(xml_file)
    cmd = VIRSH_DEFINE_CMD
    logging.debug("Command: " + str(cmd))
    print("  - Defining the Moodle VM using the updated file '{}'...".format(xml_file))
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        logging.error("Execution of the Moodle VM define command failed.")
        logging.error("Please make sure that the definition file is not corrupted.")
        logging.error("Error message: {}".format(error.output))
        sys.exit(1)

    # Run command to start VM
    # TODO: Add detection of VM name from XML file
    cmd = VIRSH_START_CMD
    logging.debug("Command: " + str(cmd))
    print("  - Starting the defined Moodle VM with identifier '{}'...".format(cmd[-1]))
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        logging.error("Execution of the Moodle VM start command failed.")
        logging.error("Please make sure that the definition file is not corrupted.")
        logging.error("Error message: {}".format(error.output))
        sys.exit(1)

    print("  STEP {}: Moodle VM set up successfully".format(step_no))


#############################################################################
# Main program
#############################################################################
def main(args):

    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='* %(levelname)s: %(filename)s: %(message)s')

    print("#########################################################################")
    print("Configuration wizard for CyLMS")
    print("#########################################################################")

    proxy_server = None
    if len(args)>0:
        proxy_server = args[0]
        logging.debug("Set proxy server to {}.".format(proxy_server))

    # Check dependencies
    step_no = 1
    check_dependencies(step_no, proxy_server)

    # Create SCORM template
    step_no += 1
    create_template(step_no, proxy_server)

    # Generate configuration file
    step_no += 1
    config_filename = generate_config(step_no)

    # Additional steps: Setup Moodle VM
    # TODO: Should this step be optional?
    step_no += 1
    setup_moodle(step_no)

    # Display final status with sample commands
    print("\n* CONFIGURATION ENDED: You can now use CyLMS as shown below:")
    print("  - Convert content in file '{}' to SCORM package".format(DEFAULT_TRAINING_FILE))
    print("    $ ./cylms.py -c {}".format(DEFAULT_TRAINING_FILE))
    print("  - Convert content to SCORM package and add it to LMS as session #{}".format(DEFAULT_SESSION_NO))
    print("    $ ./cylms.py -c {} -f {} -a {}".format(DEFAULT_TRAINING_FILE, config_filename, DEFAULT_SESSION_NO))
    print("  - Set up cyber range access via VNC for session #{}".format(DEFAULT_SESSION_NO))
    print("    $ ./cylms.py -f {} -v {}".format(config_filename, DEFAULT_SESSION_NO))
    print("  - Remove session #{} from LMS given the activity 'ID' returned when adding to LMS".format(DEFAULT_SESSION_NO))
    print("    $ ./cylms.py -f {} -r {},ID".format(config_filename, DEFAULT_SESSION_NO))


#############################################################################
# Run program
if __name__ == "__main__":
    main(sys.argv[1:])
