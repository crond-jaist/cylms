# CyLMS: Cybersecurity Training Support for LMS

CyLMS is a set of tools for adding cybersecurity training support to
Learning Management Systems (LMS). The main feature of CyLMS is
related to the conversion of a custom training content representation
in YAML format to the SCORM format that is widely used in LMSs. In
addition, CyLMS provides integration with the Moodle LMS, for
operations such as dynamically adding and removing activities to
it. CyLMS is being developed by the Cyber Range Organization and
Design (CROND) NEC-endowed chair at the Japan Advanced Institute of
Science and Technology (JAIST). An overview of CyLMS is provided in
the figure below.

![Overview of CyLMS](https://github.com/crond-jaist/cnt2lms/blob/master/cylms_overview.png)

If interested, please download the latest release of CyLMS, and let us
know if you have any issues. A sample Moodle virtual machine and a
User Guide are also provided. Note that CyLMS is mainly intended for
use in conjunction with the integrated cybersecurity training
framework CyTrONE, which is also developed by CROND at JAIST.


## Quick Start

This section provides a brief introduction on how to use CyLMS; please
refer to the User Guide for details.

### Setup

In order to setup CyLMS, the following steps are required:

* Download and extract the current release source code from GitHub:

  `$ tar -zxvf cylms-X.Y.tar.gz --directory /target/directory`

* Download and run the file "create_scorm_template.sh" to create the
  SCORM package template required by CyLMS:

  `$ /path/to/create_scorm_template.sh /full/path/to/cylms`

* Download and start the sample Moodle VM that is also provided on
  GitHub:

  `$ tar -zxvf moodle.tgz`

  `$ virsh define moodle.xml`

  `$ virsh start moodle`

  NOTE: It is also possible to set up your own Moodle host; if you
  prefer to do so, follow the instructions in the User Guide.

### Utilization

The two main operations supported by CyLMS are:

1. **Convert training content to SCORM package and add it to LMS**

  The command below converts the sample training content file
  `training_example` using the configuration file `config_example`,
  and adds the generated SCORM package to LMS as `Training Session
  #1`:

  `$ ./cylms.py --convert-content training_example.yml --config-file config_example
--add-to-lms 1`

  NOTE: The above command will display an activity id which is
  required for the operation below.

2. **Remove a training activity from LMS**

  The command below uses the configuration file `config_example` to
  remove `Training Session #1`. We denote the activity id returned by
  the `add-to-lms` operation above by `ID`, which should be replaced
  with the actual value displayed after executing the previous
  command:

  `$ ./cylms.py --config-file config_example --remove-from-lms 1,ID`


## Program overview

Below we provide a brief overview of the main CyLMS components:

* `cylms.py`: Main program used to access all the functionality
  provided by CyLMS.

* `cnt2lms`: Core module that converts a given training content
  description file to an equivalent SCORM package.

* `lms_mgmt.py`: Module that contains integration support with the
  Moodle LMS, such as adding and removing activities, etc.

* `cfg_mgmt.py`: Module used for managing the configuration file.

For your convenience we also provide some sample files:

* `training_example.yml`: Example training content file; for details
  about the training content representation used in CyLMS see the User
  Guide.

* `config_example`: Example configuration file with settings regarding
  the Moodle LMS that is to be managed via CyLMS, such as host name,
  repository directory, course name, etc. This file needs to be
  updated if you modify the provided Moodle VM, or you set up your own
  Moodle host.
