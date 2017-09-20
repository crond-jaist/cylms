# cnt2lms: Training Content to LMS Converter
cnt2lms is a tool for converting cybersecurity training content to Learning Management System (LMS) formats. Currently only the conversion to the SCORM format is supported. cnt2lms is being developed by the Cyber Range Organization and Design (CROND) NEC-endowed chair at the Japan Advanced Institute of Science and Technology (JAIST), located in Ishikawa prefecture, Japan. An overview of cnt2lms is provided in the figure below.

![Overview of cnt2lms](https://github.com/crond-jaist/cnt2lms/blob/master/cnt2lms_overview.png "Overview of cnt2lms")

If interested, please download the latest release of cnt2lms, and let us know if you have any issues. 

## How to use
Run cnt2lms.py with a configuration file:
* Example: ./cnt2lms.py config_example 

## Program modules
The program includes 3 components:
* yamlParser.py: Core module that reads a training content file and creates a SCORM package based on it
* copyToMoodle.py: Helper modules that copies the SCORM package to a Moodle repository
* cnt2lms.py: Calls the above two programs, and performs operations as specified in the configuration file

Details about the training content representation in cnt2lms are provided in the user guide, and a sample file named 'training_example.yml' is provided in the repository.

The configuration file stores information about copy or not operation, and the locations of training content file, SCORM package and Moodle repository. See the file 'config_example' for an example.

## SCORM package template
In order to operate, the cnt2lms program requires a SCORM package template. In addition to the source code, we also provide an archive containing such a template, which should be extracted in the 'Template' directory inside 'cnt2lms/'. Note that this template isbased on a package available on the SCORM website, and is distributed with a different license that the cnt2lms program (namely CC BY-SA 4.0).
