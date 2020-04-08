
#############################################################################
# VNC-based range access management for CyLMS
#############################################################################

# External imports
import sys
import subprocess
import logging

# Internal imports
import cfg_mgmt
from storyboard import Storyboard

#############################################################################
# Constants
#############################################################################

# Default range id (if not provided as argument)
RANGE_ID_DEFAULT = 1

# Constants regarding getting range info
## Tunnel creation file settings
TUNNEL_FILENAME_TEMPLATE = "{}/{}/create_tunnels.sh"
SSH_TAG = "ssh"
TUNNEL_UNIT_INDEX = 12
TUNNEL_IP_INDEX = 2
## Range details file settings
DETAILS_FILENAME_TEMPLATE = "{}/{}/range_details-cr{}.yml"
KVM_DOMAIN_TAG = "kvm_domain"
INTERFACE_TAG = "eth0"
VALUE_INDEX = 1

# Constants regarding access range file creation
ACCESS_RANGE_FILENAME_TEMPLATE="access_range{}.html"
HTML_TITLE_TEMPLATE = "<head><title>Cyber Range for Activity #{}</title></head>"
PAGE_HEADING_TEMPLATE="  <h1>Cyber Range for Activity #{}</h1>\n"
#TRAINEE_LINK_TEMPLATE="    document.write(\"<li><a href='http://\" + location.hostname + \":{}/vnc.html'>Trainee #{:02d}</a></li>\");\n"
TRAINEE_LINK_TEMPLATE="    document.write(\"<li><a href='http://\" + location.hostname + \":{}/vnc_lite.html'>Trainee #{:02d}</a></li>\");\n"
VNC_SERVER_PATH = "/root/noVNC"

# Constants regarding noVNC server start/stop
NOVNC_START_CMD_TEMPLATE = "nohup {}/utils/launch.sh --listen {} --vnc 192.168.122.1:{} > /tmp/novnc{}.out 2>&1 &"
NOVNC_STOP_CMD_TEMPLATE = "pkill --full '192.168.122.1:{}'"
RM_FILE_CMD_TEMPLATE = "rm -f {}"

# Other constants
## SSH/SCP connection options (need to be separated because of limitations on how
## options are passed to subprocess.check_output() calls)
SSH_HOSTS_NULL = "-o UserKnownHostsFile=/dev/null"
SSH_STRICT_NO = "-o StrictHostKeyChecking=no"
SSH_BGND_EXEC = "-f"

#############################################################################
# Class that contains VNC management functionality
#############################################################################
class VncManager:

    # Constructor
    def __init__(self, config_file):

        # Initialize configuration manager
        self.cfg_manager = cfg_mgmt.CfgManager(config_file)

        # Initialize internal variables
        self.lms_host = self.cfg_manager.get_setting(Storyboard.CONFIG_LMS_HOST)
        if not self.lms_host:
            logging.error("Setting not defined in config file: {} => abort".format(Storyboard.CONFIG_LMS_HOST))
            sys.exit(1)

        self.range_dir = self.cfg_manager.get_setting(Storyboard.CONFIG_RANGE_DIRECTORY)
        if not self.range_dir:
            logging.error("Setting not defined in config file: {} => abort".format(Storyboard.CONFIG_RANGE_DIRECTORY))
            sys.exit(1)

    # Get cyber range info from the files created by CyRIS
    def get_range_info(self, range_id):

        logging.info("Get info about range #{}".format(range_id))

        # Prepare tunnel creation file name
        tunnel_filename = TUNNEL_FILENAME_TEMPLATE.format(self.range_dir, range_id)

        logging.debug("  - Get entry point IP(s)")
        instance_index = 1
        tunnel_ip_addresses = []

        # Get IP addresses of entry points
        with open(tunnel_filename) as tunnel_file:
            for count,line in enumerate(tunnel_file):
                if SSH_TAG in line:
                    tunnel_ip_address = line.split(" ")[TUNNEL_UNIT_INDEX].split(":")[TUNNEL_IP_INDEX]
                    tunnel_ip_addresses.append(tunnel_ip_address)
                    instance_index += 1

        # Prepare range details file name
        details_filename = DETAILS_FILENAME_TEMPLATE.format(self.range_dir, range_id, range_id)

        logging.debug("  - Get entry point domain name(s)")
        instance_index = 1
        kvm_domains = []

        # Get IP addresses of all domains and find the domain name associated with the
        # entry point addresses determined above
        with open(details_filename) as details_file:
            for count,line in enumerate(details_file):
                if KVM_DOMAIN_TAG in line:
                    kvm_domain = line.split(":")[VALUE_INDEX].strip()
                elif INTERFACE_TAG in line:
                    ip_address = line.split(":")[VALUE_INDEX].strip()
                    if ip_address in tunnel_ip_addresses:
                        kvm_domains.append(kvm_domain)
                        instance_index += 1

        # Get VNC ports for entry points by calling 'virsh' 
        logging.debug("  - Determine entry point VNC port(s)")
        instance_index = 1
        vnc_ports = []
        for kvm_domain in kvm_domains:
            try:
                # Run virsh command to get VNC port index
                cmd_output = subprocess.check_output(["virsh", "vncdisplay", kvm_domain], stderr=subprocess.STDOUT)
                vnc_port = int(cmd_output.split(":")[1].strip()) + Storyboard.VNC_BASE_PORT
                vnc_ports.append(vnc_port)
            except subprocess.CalledProcessError as error:
                logging.error("Failed to get VNC port for domain '{}'\n  Error message: {}".format(kvm_domain, error.output.rstrip()))
                return None
            
            instance_index += 1

        logging.info("- Returned list of VNC ports: {}".format(str(vnc_ports)))
        return vnc_ports

    # Create the access range file
    def create_access_file(self, range_id, vnc_ports):

        # Prepare access range file name
        access_range_filename = ACCESS_RANGE_FILENAME_TEMPLATE.format(range_id)

        logging.info("Create range access file '{}'".format(access_range_filename))

        # Write content to HTML file
        with open(access_range_filename, 'w') as access_range_file:

            logging.debug("  - Write content to file '{}'".format(access_range_filename))

            # Write HTML file header
            access_range_file.write("<!DOCTYPE html>\n")
            access_range_file.write("<html>\n")
            access_range_file.write(HTML_TITLE_TEMPLATE.format(range_id))
            access_range_file.write("<body>\n")

            # Write HTML file body
            access_range_file.write(PAGE_HEADING_TEMPLATE.format(range_id))
            access_range_file.write("  <h2><ul><script>\n")
            trainee_index = 1
            for vnc_port in vnc_ports:
                range_port = vnc_port - Storyboard.VNC_BASE_PORT + Storyboard.ACCESS_RANGE_BASE_PORT
                access_range_file.write(TRAINEE_LINK_TEMPLATE.format(range_port, trainee_index))
                trainee_index += 1
            access_range_file.write("  </script></ul></h2>\n")

            # Write HTML file footer
            access_range_file.write("</body>\n")
            access_range_file.write("</html>\n")

            # Make sure to flush content to file before proceeding to copy
            access_range_file.flush()

        # Copy access range file to Moodle server 
        logging.debug("  - Copy range file to Moodle server")
        destination_path = self.lms_host + ":" + VNC_SERVER_PATH 
        try:
            cmd_output = subprocess.check_output(
                ["scp", SSH_HOSTS_NULL, SSH_STRICT_NO, access_range_filename, destination_path],
                stderr=subprocess.STDOUT)

        # Any execution error will lead to an exception, which we handle below
        except subprocess.CalledProcessError as error:
            logging.error("Error when copying file '{}' to '{}'\n  Error message: {}"
                          .format(access_range_filename, destination_path, error.output.rstrip()))
            return False

        logging.info("- Copied file to '{}'".format(destination_path))
        return True

    # Start the noVNC servers
    def start_novnc_servers(self, vnc_ports):

        logging.info("Start noVNC servers on '{}'".format(self.lms_host))

        # Start servers
        access_range_ports = []
        for vnc_port in vnc_ports:
            access_range_port = vnc_port - Storyboard.VNC_BASE_PORT + Storyboard.ACCESS_RANGE_BASE_PORT
            access_range_ports.append(access_range_port)
            novnc_start_cmd = NOVNC_START_CMD_TEMPLATE.format(VNC_SERVER_PATH, access_range_port, vnc_port, access_range_port)
            try:
                cmd_output = subprocess.check_output(
                    ["ssh", SSH_HOSTS_NULL, SSH_STRICT_NO, SSH_BGND_EXEC, self.lms_host, novnc_start_cmd],
                    stderr=subprocess.STDOUT)

            # Any execution error will lead to an exception, which we handle below
            except subprocess.CalledProcessError as error:
                logging.error("Error when starting noVNC servers on '{}'\n  Error message: {}"
                              .format(self.lms_host, error.output.rstrip()))
                return False

        logging.info("- Started noVNC server(s) on port(s): {}".format(access_range_ports))        
        return True

    # Stop the noVNC servers
    def stop_novnc_servers(self, range_id, vnc_ports):

        logging.info("Stop noVNC servers on '{}'".format(self.lms_host))

        # Remove access range file from server
        file_name = VNC_SERVER_PATH + "/" + ACCESS_RANGE_FILENAME_TEMPLATE.format(range_id)
        rm_file_cmd = RM_FILE_CMD_TEMPLATE.format(file_name)
        try:
            cmd_output = subprocess.check_output(
                ["ssh", SSH_HOSTS_NULL, SSH_STRICT_NO, self.lms_host, rm_file_cmd],
                stderr=subprocess.STDOUT)

        # Any execution error will lead to an exception, which we handle below
        except subprocess.CalledProcessError as error:
            logging.error("Error when removing access range file from '{}'\n  Error message: {}"
                          .format(self.lms_host, error.output.rstrip()))

        # Stop servers
        for vnc_port in vnc_ports:
            novnc_stop_cmd = NOVNC_STOP_CMD_TEMPLATE.format(vnc_port)
            try:
                cmd_output = subprocess.check_output(
                    ["ssh", SSH_HOSTS_NULL, SSH_STRICT_NO, self.lms_host, novnc_stop_cmd],
                    stderr=subprocess.STDOUT)

            # Any execution error will lead to an exception, which we handle below
            except subprocess.CalledProcessError as error:
                logging.error("Error when stopping noVNC servers on '{}'\n  Error message: {}"
                              .format(self.lms_host, error.output.rstrip()))
                return False

        logging.info("- Stopped noVNC server(s) on port(s): {}".format(vnc_ports))
        return True


#############################################################################
# Main program (used for testing purposes)
#############################################################################
def main(args):

    # Configure logging level for running the tests below
    logging.basicConfig(level=logging.INFO,
                        format='* %(levelname)s: %(filename)s: %(message)s')

    # Get arguments (if any)
    if len(args) >= 1:
        range_id = args[0]
    else:
        range_id = RANGE_ID_DEFAULT

    # Create a VNC manager object
    vnc_manager = VncManager(Storyboard.DEFAULT_CONFIG_FILE)

    START = True
    if START:
        vnc_ports = vnc_manager.get_range_info(range_id)
        if vnc_ports:
            if vnc_manager.create_access_file(range_id, vnc_ports):
                if not vnc_manager.start_novnc_servers(vnc_ports):
                    logging.error("Failed to start VNC servers => abort VNC setup")
            else:
                logging.error("Failed to create range access file => abort VNC setup")
        else:
            logging.error("Failed to get cyber range info => abort VNC setup")
    else:
        vnc_ports = vnc_manager.get_range_info(range_id)
        if vnc_ports:
            if not vnc_manager.stop_novnc_servers(range_id, vnc_ports):
                logging.error("Failed to stop VNC servers => abort VNC setup")
        else:
            logging.error("Failed to get cyber range info => abort VNC setup")


#############################################################################
# Run program
if __name__ == "__main__":
    main(sys.argv[1:])
