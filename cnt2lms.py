#!/usr/bin/env python
"""
cnt2lms.py
"""
import os
import sys
import re
import logging
from yamlParser import yamlToSCORM as converter
from copyToMoodle import copyFunction as copy

logging.basicConfig(level=logging.DEBUG, \
#                    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
                    format='* %(levelname)s: %(filename)s: %(message)s')

def main():
    """
    Main function of the program, which call yamlParser.py and copyToMoodle.py
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    #Print banner
    #Read version from a CHANGES file
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

    config = "config_example"

    config = str(dir_path) + "/" + config

    #Input yaml file
    try:
        config = sys.argv[1]
    except:
        logging.info("Please specify a configuration file. Example: ./cnt2lms.py my_config")
        logging.info("Using default configuration file: " + str(config))
    converter(config,dir_path)
    copy(config)

if __name__ == "__main__":
    main()
