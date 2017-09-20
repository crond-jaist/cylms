#!/usr/bin/env python

import yamlParser

import os
import sys
import logging
logging.basicConfig(level=logging.DEBUG, \
#                   format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
                   format='* %(levelname)s: %(filename)s: %(message)s')

def copyFunction(config):
    if yamlParser.readConfigFile(config,'copy') == '1':
        logging.info("Copy from: " + yamlParser.readConfigFile(config,'package_name'))
        logging.info("Copy to: " + yamlParser.readConfigFile(config,'destination'))
    yamlParser.copyToRepository(yamlParser.readConfigFile(config,'copy'),yamlParser.readConfigFile(config,'package_name'), yamlParser.readConfigFile(config,'destination'))

def main():
    config = "config"

    dir_path = os.path.dirname(os.path.realpath(__file__))

    config = str(dir_path) + "/" + config

    #Input yaml file
    try:
        config = sys.argv[1]
    except:
                logging.info("Please specify a configuration file. Example: ./copyToMoodle.py my_config")
                logging.info("Using default configuration file: " + str(config))
    copyFunction(config)

if __name__ == "__main__":
    main()
