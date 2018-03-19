#!/usr/bin/env python
"""
cnt2lms.py
"""
import os
import sys
import re
import logging

from yamlParser import yamlToSCORM
from copyToMoodle import copyPackage
from storyboard import Storyboard

# Configure logging
logging.basicConfig(level=logging.DEBUG, \
                    format='* %(levelname)s: %(filename)s: %(message)s')

def main():
    """
    Main function of the program, which calls yamlParser.py and copyToMoodle.py
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Print banner (read version from CHANGES file)
    changes_filename = str(dir_path) + "/CHANGES"
    try:
        changes_file = open(changes_filename)
        for line in changes_file:
            if re.match('cnt2lms v', line.lower()):
                VERSION = line.rstrip('\n')
                break
    except:
        VERSION = 'cnt2lms'

    print("#########################################################################")
    print("%s: Training content to LMS converter" % (VERSION))
    print("#########################################################################")

    config_file = Storyboard.DEFAULT_CONFIG_FILE
    config_file = str(dir_path) + "/" + config_file

    # Get the configuration file from command line (if any)
    try:
        config_file = sys.argv[1]
    except:
        logging.info("It is recommended to specify a configuration file. ./cnt2lms.py <config_file>")
        logging.info("Currently using the default configuration file: " + str(config_file))

    # Perform YAML to SCORM package conversion and optional copy operations
    yamlToSCORM(config_file, dir_path)
    copyPackage(config_file)

if __name__ == "__main__":
    main()
