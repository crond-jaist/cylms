# CyLMS: Cybersecurity Training Support for LMS

CyLMS is a set of tools that adds cybersecurity training support to
Learning Management Systems (LMSs). The main function of CyLMS is to
convert a custom training content representation provided in YAML
format into the SCORM format that is widely supported by LMSs. In
addition, CyLMS provides integration with the Moodle LMS, for
operations such as dynamically adding and removing training activities
to it. CyLMS is being developed by the Cyber Range Organization and
Design (CROND) NEC-endowed chair at the Japan Advanced Institute of
Science and Technology (JAIST). An overview of CyLMS is provided in
the figure below.

![Overview of CyLMS](https://github.com/crond-jaist/cylms/blob/master/cylms_overview.png)

More details about CyLMS are available in the User Guide published on
the [releases](https://github.com/crond-jaist/cylms/releases) page
that also includes the latest stable version of the software. We also
provide a sample Moodle virtual machine as a convenient way to quickly
start using our software. Note that CyLMS is mainly intended for use
in conjunction with the integrated cybersecurity training framework
[CyTrONE](https://github.com/crond-jaist/cytrone) that is also
developed by CROND at JAIST.


## Setup

The following steps are required to setup CyLMS:

1. Download the next three files from the latest
   [release](https://github.com/crond-jaist/cylms/releases) of CyLMS
   on GitHub:

   - `create scorm template.sh`: Self-extractable archive for
     creating a SCORM package template
   - `moodle.tgz`: Archive containing the sample Moodle VM that can be
     used to get started with CyLMS
   - `cylms-X.Y.tar.gz` (where X.Y is the version number): Source code
     of CyLMS, available via the link "Source code (tar.gz)"

2. Extract `cylms-X.Y.tar.gz` and `moodle.tgz` into the target
   directory of your choice, such as `/home/cyuser`:

   `$ tar -xzf cylms-X.Y.tar.gz --directory /target/directory`

   `$ tar -xzf moodle.tgz --directory /target/directory/cylms`

3. Run the configuration script `configure.py` to finish setting up
   CyLMS:

   `$ ./configure.py`


## Utilization

The two main operations supported by CyLMS are:

1. **Convert training content to SCORM package and add it to LMS**

   The command below converts the sample training content file
   `training_example.yml` using the configuration file `config_file`,
   and adds the generated SCORM package to LMS as "Activity #1:
   Example questions":

   `$ ./cylms.py --convert-content training_example.yml --config-file config_file --add-to-lms 1`

   NOTE: The command above will display an activity id which is
   required for the operation below.

2. **Remove a training session from LMS**

   The next command uses the configuration file `config_file` to
   remove the created activity. We denote the activity id returned by
   the `add-to-lms` operation above by `ID`, but it should be replaced
   with the actual value displayed after executing the previous
   command:

   `$ ./cylms.py --config-file config_file --remove-from-lms 1,ID`

For further details, including on how to set up cyber range access via
VNC so that trainees can access the training enviornment associated to
a certain learning content more conveniently, please refer to the User
Guide.


## Sample files

In addition to the source code, so sample files are provided for your
convenience:

* `demo quiz.yml` and `training_example.yml`: Example training content
  files; for details about the training content representation used in
  CyLMS see the User Guide
* `config_example`: Example configuration file with settings regarding
  the Moodle LMS that is to be managed via CyLMS, such as host name,
  repository directory, course name, etc. This file needs to be
  updated if you modify the provided Moodle VM, or you set up your own
  Moodle host


## References

For a research background regarding CyLMS, please refer to the
following paper:

* R. Beuran, D. Tang, Z. Tan, S. Hasegawa, Y. Tan, Y. Shinoda,
  "Supporting Cybersecurity Education and Training via LMS
  Integration: CyLMS", Springer Education and Information
  Technologies, November 2019, vol. 24, no. 6, pp. 3619-3643.

For a list of contributors to this project, please check the file
CONTRIBUTORS included with the source code.

