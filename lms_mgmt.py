#!/usr/bin/env python

#############################################################################
# LMS management functionality for CyLMS
#############################################################################

# External imports
#import sys
import subprocess
import logging
import os

# Internal imports
import cfg_mgmt
from storyboard import Storyboard

#############################################################################
# Constants
#############################################################################

## Simulation mode flag for testing purposes
SIMULATION_MODE = False

## Moosh-related constants
MOOSH_COMMAND = "moosh/moosh.php -p /var/www/html/moodle/"
ACTIVITY_ID_FIELD = "cmid="
### Constants below are  based on values from /var/www/html/moodle/mod/scorm/locallib.php
PACKAGEFILEPATH_OPTION = "packagefilepath"
INTRO_OPTION ="intro"
UPDATEFREQ_OPTION = "updatefreq"
SCORM_UPDATE_EVERYTIME = 3

## Test action-related constants
GET_ID_ACTION = 0
ADD_ACTION = 1
DELETE_ACTION = 2
COPY_ACTION = 3


#############################################################################
# Class that contains LMS management functionality
#############################################################################
class LmsManager:

    # Constructor
    def __init__(self, config_file):

        # Initialize configuration manager
        self.cfg_manager = cfg_mgmt.CfgManager(config_file)

        # Initialize internal variables
        self.lms_host = self.cfg_manager.get_setting(Storyboard.CONFIG_LMS_HOST)
        self.lms_repository = self.cfg_manager.get_setting(Storyboard.CONFIG_LMS_REPOSITORY)
        self.course_name = self.cfg_manager.get_setting(Storyboard.CONFIG_COURSE_NAME)
        self.section_id = self.cfg_manager.get_setting(Storyboard.CONFIG_SECTION_ID)

        # Display debug info
        logging.debug("LMS manager settings:")
        logging.debug("  - LMS host: {}".format(self.lms_host))
        logging.debug("  - LMS repository: {}".format(self.lms_repository))
        logging.debug("  - Course name: {}".format(self.course_name))
        logging.debug("  - Section id: {}".format(self.section_id))

    # Get the id of the course with given name
    def get_course_id(self):

        if SIMULATION_MODE:
            course_id = 999
            logging.debug("Simulation mode: Matching course id: {}".format(course_id))
            return course_id
        else:
            # Get course list
            ssh_output = subprocess.check_output(["ssh", self.lms_host, MOOSH_COMMAND, "course-list"])
            logging.debug("Course list output: {}".format(ssh_output.rstrip()))

            # Find the appropriate course
            for output_line in ssh_output.splitlines():
                # Extract the course id
                if self.course_name in output_line:
                    logging.debug("Matching course info: {}".format(output_line.rstrip()))
                    # Split line of form "2","Top/CROND","CyTrONE Training","CyTrONE Training","1"
                    course_id = output_line.split(",")[0]
                    # Split id string of form "2"
                    course_id = course_id.split('"')[1]
                    logging.debug("Extracted id of matching course: {}".format(course_id))
                    return course_id

            # If we reach this point, it means the course name was not found
            logging.error("No matching record for course '{}'".format(self.course_name))
            return None

    # Add an activity based on course id, section id and package file
    def add_activity(self, activity_name, package_file):

        if SIMULATION_MODE:
            logging.debug("Simulation mode: Add activity '{}'.".format(activity_name))
            activity_id = 99
            return activity_id
        else:
            # Get the course id
            course_id = self.get_course_id()
            if course_id:
                logging.debug("Retrieved id for course '{}': {}".format(self.course_name, course_id))

                try:
                    # Add repository prefix to target file
                    package_file = self.lms_repository + package_file
                    options_string = PACKAGEFILEPATH_OPTION + "=" + package_file + "," \
                                     + UPDATEFREQ_OPTION + "=" + str(SCORM_UPDATE_EVERYTIME) + "," \
                                     + INTRO_OPTION +"='" + activity_name + "'"
                    ssh_output = subprocess.check_output(
                        ["ssh", self.lms_host, MOOSH_COMMAND, "activity-add",
                         "--section " + self.section_id, "--name '" + activity_name + "'",
                         "--options " + options_string, "scorm", course_id],
                        stderr=subprocess.STDOUT)
                    logging.debug("Add activity output: {}".format(ssh_output.rstrip()))

                    # Determine the activity id
                    for output_line in ssh_output.splitlines():
                        # Extract the activity id from cmid line
                        if ACTIVITY_ID_FIELD in output_line:
                            activity_id = output_line.split("=")[1]
                            if activity_id:
                                logging.info("Added activity for course id '{}' section id '{}' with name '{}' => id is {}."
                                             .format(course_id, self.section_id, activity_name, activity_id))
                                return activity_id

                    # If we reach this point, it means an error occurred
                    logging.error("Error when determining the activity id\n  Command output: {}".format(ssh_output))
                    return None

                # Any execution error will lead to an exception, which we handle below
                except subprocess.CalledProcessError as error:
                    logging.error("Error when adding activity for course id '{}' section id '{}'\n  Error message: {}"
                                  .format(course_id, self.section_id, error.output))

                    return None

            # If we reach this point, an error occurred
            logging.error("Failed to add activity for course '{}'.".format(self.course_name))
            return None

    # Delete an activity with given id
    def delete_activity(self, activity_id, package_file):
        if SIMULATION_MODE:
            logging.debug("Simulation mode: Delete activity with id '{}'.".format(activity_id))
            return True
        else:
            # Delete activity
            try:
                ssh_output = subprocess.check_output(["ssh", self.lms_host, MOOSH_COMMAND,
                                                      "activity-delete", str(activity_id)],
                                                     stderr=subprocess.STDOUT)
                logging.debug("Delete activity output: {}".format(ssh_output.rstrip()))

                # If deletion succeeds, we also remove the associated package file
                package_file = self.lms_repository + package_file
                rm_output = subprocess.check_output(["ssh", self.lms_host, "rm", package_file],
                                                    stderr=subprocess.STDOUT)

                # If we reach this point, it means no error occured
                return True

            # Any execution error will lead to an exception, which we handle below
            except subprocess.CalledProcessError as error:
                logging.error("Error when deleting activity with id '{}'\n  Error message: {}"
                              .format(activity_id, error.output.rstrip()))
                return False

    # Copy the SCORM package to Moodle according to configuration file options
    def copy_package(self, package_file, target_file):

        # Add repository prefix to target file
        target_file = self.lms_repository + target_file
        
        if SIMULATION_MODE:
            logging.info("Simulation mode: Copy package '{}' to\n\tTarget '{}'.".format(package_file, target_file))
            return True
        else:
            # Display operation info
            logging.info("Copy package '{}' to\n\tTarget '{}'.".format(package_file, target_file))
            command = "scp -q {} {}:{}".format(package_file, self.lms_host, target_file)
            logging.debug("Copy command: {}".format(command))
            return_value = os.system(command)
            exit_status = os.WEXITSTATUS(return_value)
            if exit_status != 0:
                logging.error("Copy package operation failed.")
                return False

            return True


#############################################################################
# Main program (used for testing purposes)
#############################################################################
def main():

    # Configure logging level for running the tests below
    logging.basicConfig(level=logging.INFO,
                        format='* %(levelname)s: %(filename)s: %(message)s')

    # Create an LMS manager object
    lms_manager = LmsManager(Storyboard.DEFAULT_CONFIG_FILE)

    # Define action
    action = GET_ID_ACTION
    #action = ADD_ACTION
    #action = DELETE_ACTION
    #action = COPY_ACTION
    
    # Perform actions
    ## Get course id
    if action == GET_ID_ACTION:
        course_id = lms_manager.get_course_id()
        if course_id:
            logging.info("Retrieved id for course with name '{}': {}".format(lms_manager.course_name, course_id))
        else:
            logging.error("Failed to get id for course '{}'.".format(lms_manager.course_name))
            quit(-1)            
        
    ## Add activity
    elif action == ADD_ACTION:
        activity_name = "Training Session #99"
        package_file = "training_example.yml.zip"
        activity_id = lms_manager.add_activity(activity_name, package_file)
        if activity_id:
            logging.info("Added activity with id '{}'.".format(activity_id))
        else:
            logging.error("Failed to add activity '{}'.".format(activity_name))
            quit(-1)

    ## Delete activity
    elif action == DELETE_ACTION:
        activity_id = 99
        package_file = "training_example.yml.zip"
        success_status = lms_manager.delete_activity(activity_id, package_file)
        if success_status:
            logging.info("Deleted activity with id '{}'.".format(activity_id))
        else:
            logging.error("Failed to delete activity with id '{}'.".format(activity_id))
            quit(-1)

    ## Copy package
    elif action == COPY_ACTION:
        package_file = "training_example.yml.zip"
        target_file = package_file
        success_status = lms_manager.copy_package(package_file, target_file)
        if success_status:
            logging.info("Copied package '{}' to LMS repository.".format(package_file))
        else:
            logging.error("Failed to copy package '{}'.".format(package_file))
            quit(-1)
    
    else:
        logging.error("No action was selected => do nothing.")


#############################################################################
# Run main program
#############################################################################
if __name__ == "__main__":
    main()
