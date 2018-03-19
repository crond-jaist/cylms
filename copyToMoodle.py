#!/usr/bin/env python

import os
import sys
import ConfigParser
import logging

from storyboard import Storyboard

# Configure logging
logging.basicConfig(level=logging.DEBUG, \
                   format='* %(levelname)s: %(filename)s: %(message)s')

# Get option from configuration file
# (return None if option is not present)
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

# Copy the SCORM package to Moodle according to configuration file options
def copyPackage(config_file):

    # Check whether the copy operation is enabled
    if getOption(config_file, Storyboard.CONFIG_ENABLE_COPY):

        # Display operation info
        package_name = getOption(config_file, Storyboard.CONFIG_PACKAGE_NAME)
        logging.info("Copy from: {}".format(package_name))
        remote_lms = getOption(config_file, Storyboard.CONFIG_REMOTE_LMS)
        if remote_lms:
            method = "scp"
        else:
            method = "cp"
        destination = getOption(config_file, Storyboard.CONFIG_DESTINATION)
        logging.info("Do {} to: {}".format(method, destination))

        # Perform the copy operation
        if remote_lms:
            command = "scp -q {} {}:{}".format(package_name, remote_lms, destination)
        else:
            command = "cp -f {} {}".format(package_name, destination)
        return_value = os.system(command)
        exit_status = os.WEXITSTATUS(return_value)
        if exit_status != 0:
            logging.error("SCORM package copy operation failed.")
            quit(-1)

def main():

    # Set up the default configuration file
    config_file = Storyboard.DEFAULT_CONFIG_FILE
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_file = str(dir_path) + "/" + config_file

    # Get the configuration file from command line (if any)
    try:
        config_file = sys.argv[1]
    except:
        logging.info("It is recommended to specify a configuration file: ./copyToMoodle.py <config_file>")
        logging.info("Currently using the default configuration file: " + str(config_file))

    # Perform the package copy operation
    copyPackage(config_file)

if __name__ == "__main__":
    main()
