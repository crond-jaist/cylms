#!/usr/bin/env python

import os
import re
import sys
import paramiko

def sftp_init(cyris_machine, cyris_user, key_location):
    # Setup key
    my_key = paramiko.RSAKey.from_private_key_file(key_location)
    
    # Open a connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(cyris_machine, username= cyris_user, pkey= my_key)
    
    # Create an sftp session
    ftp = ssh.open_sftp()
    return ftp

def sftp_close(ftp):
    ssh = ftp.get_channel()
    ftp.close()
    ssh.close()    


def download_cr_file(cyris_machine, cyris_user, cr_dir , local_dir, file_name, key_location):
    # This function look at cyberrange directory and
    #+find a specific file.

    # Create an sftp session
    ftp = sftp_init(cyris_machine, cyris_user, key_location)
    # Access cyberrange dir
    ftp.chdir(cr_dir)
    files = ftp.listdir()

    # Check if an element is a directory
    for i in files:
        my_lstat = str(ftp.lstat(i)).split()[0]
        if "d" in my_lstat:
            # Change dir to a cyberrange's dir
            ftp.chdir(ftp.getcwd() + "/" + i)
            for j in ftp.listdir():
                if file_name in j:
                    ftp.get(j,local_dir + "/" + j)
            # Change dir back to main cyberrange dir
            ftp.chdir(cr_dir)
    sftp_close(ftp)

def get_cr_noti(cyris_machine, cyris_user, cr_dir, local_dir):
    download_cr_file(cyris_machine, cyris_user, cr_dir, local_dir, "range_notification")

def get_cr_details(cyris_machine, cyris_user, cr_dir, local_dir):
    download_cr_file(cyris_machine, cyris_user, cr_dir, local_dir, "range_details")

def parse_all_noti(f, local_dir):
    script_template = "#!/bin/sh \nsshpass -p 'password' command -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
    file_prefix = "connect_to_cyber_range_"
    content = f.read()
    # Search for the cyberrange ID 
    match = re.search(r'.*Training Session #(\w+)', content)
    if match: cr_id = match.group(1)

    # Search for each instance and create a script to connect
    #+to the cyberrange automatically
    match = re.findall(r'.*Cyber range instance #(\d+).*\n.*Login: ([\S+ ]+)\n.*Password: (\S+)', content) 
    if match:
        for i in match:
            script = script_template.replace('password', i[2])
            script = script.replace('command', i[1])
            
            # Create a new script file using sshpass to connect
            #+to each cyberrange
            file_name = local_dir + '/' + file_prefix + cr_id + '_' + i[0] + '.sh'
            with open(file_name, 'w') as out_f:
                print "* INFO: get_cyris_result.py: Generated script: " + str(file_name.replace('.sh',''))
                out_f.write(script)

            # Make binary files from scipts created above
            os.system('shc -r -f ' + file_name + ' -o ' + file_name.replace('.sh',''))
            # Delele the script file after compling it
            os.remove(file_name)
            os.remove(file_name.replace('.sh','.sh.x.c'))

def parse_one_noti(f, local_dir, ins_id):
    # This is a clone of parse_all_noti, but only parse 1 instance
    script_template = "#!/bin/sh \nsshpass -p 'password' command -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
    file_prefix = "connect_to_cyber_range_"
    content = f.read()
    # Search for the cyberrange ID 
    match = re.search(r'.*Training Session #(\w+)', content)
    if match: cr_id = match.group(1)

    # Search for each instance and create a script to connect
    #+to the cyberrange automatically
    match = re.search(r'.*Cyber range instance #(\d+).*\n.*Login: ([\S+ ]+)\n.*Password: (\S+)', content) 
    if match:
        i = match.groups()
        if i[0] == ins_id:
            script = script_template.replace('password', i[2])
            script = script.replace('command', i[1])
            
            # Create a new script file using sshpass to connect
            #+to each cyberrange
            file_name = local_dir + '/' + file_prefix + cr_id + '_' + i[0] + '.sh'
            with open(file_name, 'w') as out_f:
                print "* INFO: get_cyris_result.py: Generated script: " + str(file_name.replace('.sh',''))
                out_f.write(script)
            
            # Make binary files from scipts created above
            os.system('shc -r -f ' + file_name + ' -o ' + file_name.replace('.sh',''))
            os.system('sudo /usr/bin/chown trainee01 ' + file_name.replace('.sh',''))
            # Delele the script file after compling it
            os.remove(file_name)
            os.remove(file_name.replace('.sh','.sh.x.c'))

def find_all_noti(cyris_machine, cyris_user, cr_dir, local_dir, key_location):
    # This function look at cyberrange directory and
    #+find notification files.

    file_name_prefix = "range_notification"

    # Create an sftp session
    ftp = sftp_init(cyris_machine, cyris_user, key_location)
    # Access cyberrange dir
    ftp.chdir(cr_dir)
    files = ftp.listdir()

    count = 0
    # Check if an element is a directory
    for i in files:
        my_lstat = str(ftp.lstat(i)).split()[0]
        if "d" in my_lstat:
            # Change dir to a cyberrange's dir
            ftp.chdir(ftp.getcwd() + "/" + i)
            for j in ftp.listdir():
                if file_name_prefix in j:
                    count += 1
                    with ftp.file(j) as f:
                        parse_all_noti(f, local_dir)
            # Change dir back to main cyberrange dir
            ftp.chdir(cr_dir)
    sftp_close(ftp)            
    
    if count == 0:
        print "* INFO: get_cyris_result.py: There is no cyber range now"

def find_one_noti(cyris_machine, cyris_user, cr_dir, local_dir, key_location, cr_id, ins_id):
    # This is a clone of find_all_noti fuction, but only create the scripts for the
    #+specify cyberrange instance.
    # This function look at cyberrange directory and
    #+find notification files.

    file_name_prefix = "range_notification-cr"

    # Create an sftp session
    ftp = sftp_init(cyris_machine, cyris_user, key_location)
    # Access cyberrange dir
    ftp.chdir(cr_dir)

    try:
        ftp.chdir(ftp.getcwd() + "/" + cr_id)
    except:
        print "* INFO: get_cyris_result.py: The cyber range does not exist" 
    
    with ftp.file(file_name_prefix + cr_id + ".txt") as f:
        parse_one_noti(f, local_dir, ins_id)
    # Change dir back to main cyberrange dir
    ftp.chdir(cr_dir)
    sftp_close(ftp)            
    
def main():
    CYRIS_MACHINE = "172.16.1.3"
    CYRIS_USER = "crond"
    CR_DIR = "/home/crond/cyris-devel/cyber_range"
    # Where to store downloaded and created files 
    LOCAL_DIR = "/home/trainee01"    
    KEY_LOCATION = "/home/crond/.ssh/id_rsa"    

#    get_cr_noti(CYRIS_MACHINE, CYRIS_USER, CR_DIR, LOCAL_DIR)
#    get_cr_details(CYRIS_MACHINE, CYRIS_USER, CR_DIR, LOCAL_DIR)
    if len(sys.argv) != 6:
        print "You should specify CYRIS_MACHINE, CYRIS_USER, CR_DIR"
        print "Example: ./get_cyris_result.py \"172.16.1.3\" \"crond\"  \"/home/crond/cyris-devel/cyber_range\" 5 1"
    else:
        CYRIS_MACHINE = sys.argv[1]
        CYRIS_USER = sys.argv[2]
        CR_DIR =  sys.argv[3]
        CR_ID = sys.argv[4]
        INS_ID = sys.argv[5]

        find_one_noti(CYRIS_MACHINE, CYRIS_USER, CR_DIR, LOCAL_DIR, KEY_LOCATION, CR_ID, INS_ID)
if __name__ == '__main__':
    main()
