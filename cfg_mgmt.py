
#############################################################################
# Configuration file management for CyLMS
#############################################################################

# External imports
import logging
import ConfigParser

# Internal imports
from storyboard import Storyboard


#############################################################################
# Class that contains management functionality for configuration files
#############################################################################
class CfgManager:

    # Constructor
    def __init__(self, config_file):
        # Initialize configuration parser from config_file
        self.config_parser = ConfigParser.ConfigParser()
        logging.debug("Initialize configuration manager from file '{}'.".format(config_file))
        config_file_list = self.config_parser.read(config_file)
        # Check whether the configuration file could be read 
        if config_file_list:
            if not self.config_parser.has_section(Storyboard.CONFIG_SECTION):
                logging.error("Configuration file doesn't contain required section '{}' => abort execution.".format(Storyboard.CONFIG_SECTION))
                quit(-1)
        else:
            logging.error("Cannot read configuration file '{}' => abort execution.".format(config_file))
            quit(-1)
        
    # Get value of given setting from the configuration file;
    # return None if setting is not present
    def get_setting(self, setting):
        if self.config_parser:
            if self.config_parser.has_option(Storyboard.CONFIG_SECTION, setting):
                logging.debug("Setting '{}' present in configuration file.".format(setting))
                # Some settings could be treated in a special manner
#                if setting == Storyboard.CONFIG_ENABLE_COPY:
#                    return self.config_parser.getboolean(Storyboard.CONFIG_SECTION, setting)
                return self.config_parser.get(Storyboard.CONFIG_SECTION, setting)
            else:
                return None
        else:
            logging.error("Invalid configuration parser => abort execution.")
            quit(-1)


#############################################################################
# Main program (used for testing purposes)
#############################################################################
def main():

    # Configure logging level for running the tests below
    logging.basicConfig(level=logging.INFO,
                        format='* %(levelname)s: %(filename)s: %(message)s')

    # Create configuration manager object
    config_file = Storyboard.DEFAULT_CONFIG_FILE
    logging.info("Read configuration from file '{}'.".format(config_file))
    cfg_manager = CfgManager(config_file)

    # Create list of known settings
    setting_list = [Storyboard.CONFIG_LMS_HOST, Storyboard.CONFIG_LMS_REPOSITORY,
                    Storyboard.CONFIG_COURSE_NAME, Storyboard.CONFIG_SECTION_ID]

    # Show all settings in list and their values
    logging.info("Current program settings and their values:")
    for setting in setting_list:
        logging.info("  - {}: {}"
                     .format(setting, cfg_manager.get_setting(setting)))


#############################################################################
# Run main program
#############################################################################
if __name__ == "__main__":
    main()
