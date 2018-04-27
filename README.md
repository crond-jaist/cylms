# CyLMS: Cybersecurity Training Support for LMS

CyLMS is a set of tools for adding cybersecurity training support to
Learning Management Systems (LMS). The main feature of CyLMS is
related to the conversion of training content representation in YAML
format to the SCORM format which is widely used in LMSs. In addition,
CyLMS provides a certain integration with the Moodle LMS, for
operations such as dynamically adding and removing activities to
it. CyLMS is being developed by the Cyber Range Organization and
Design (CROND) NEC-endowed chair at the Japan Advanced Institute of
Science and Technology (JAIST). An overview of CyLMS is provided in
the figure below.

![Overview of CyLMS](https://github.com/crond-jaist/cylms/blob/master/cylms_overview.png "Overview of CyLMS")

If interested, please download the latest release of CyLMS, and let us
know if you have any issues. A sample Moodle virtual machine and a
User Guide are also provided. Note that CyLMS is mainly intended for
use in conjunction with the integrated cybersecurity training
framework CyTrONE, which is also developed by CROND at JAIST.

## Quick Start

This section provides a brief introduction on how to use CyLMS.

### Setup
In order to setup CyLMS, the following steps are required:

* Download and extract the current release source code from GitHub

* Download and run the file "create_scorm_template.sh" to create the
  SCORM package template required by CyLMS:
  $ /path/to/create_scorm_template.sh /full/path/to/cylms

* Create a configuration file with details about the LMS host, course
  name, etc. If you are using the provided Moodle VM, the sample
  "config_example" can be used as such. Otherwise you will need to set
  up your own Moodle host (for details see the User Guide)

### Basic operation

There are two main operations possible via CyLMS:

* Convert a training content file to SCORM package and add it to
  LMS. The example below converts the sample content file
  "training_example" using the configuration file "config_example" and
  adds the generated SCORM package to LMS as training session #1:

  $ ./cylms.py --convert-content training_example.yml --config-file config_example
--add-to-lms 1

* Remove a training activity from LMS. The example below uses again
the configuration file "config_example" and removes training session
#1, assuming the activity id returned by the add-to-lms command was
"10" (this needs to be change based on the actual returned value when
you execute the previous command)

 $ ./cylms.py --config-file config_example --remove-from-lms 1,10
 
## Program overview

Below we provide a brief overview of CyLMS. The tool set includes
several components:

* cylms: Main program of the tool set which is used to provide all the
  functionality implemented in the other modules
* cnt2lms: Core module that converts a given training content
  description file to an equivalent SCORM pacage
* lms_mgmt.py: Module that containt management functionality related
  to LMS, such as adding and removing activities, etc.
* cfg_mgmt.py: Module for managing the configuration files

Details about the training content representation used in CyLMS are
provided in the User Guide, and a sample training content file named
'training_example.yml' is provided with the source code.

The configuration file contains settings regarding the LMS that is to
be managed via CyLMS, such as host name, repository directory, related
course name, etc. See the file 'config_example' for an example.
