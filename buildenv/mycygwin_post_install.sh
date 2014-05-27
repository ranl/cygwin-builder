#!/bin/bash

set -e
export PATH=/usr/bin:$PATH

# Configure local permission
chmod +r /etc/passwd
chmod +r /etc/group
chmod 755 /var

# Configure username & groups
mkpasswd.exe -l > /etc/passwd
mkgroup.exe -l > /etc/group

# Configure SSH
net stop sshd || true
cygrunsrv -R sshd || true
net user sshd /delete /y || true
ssh_password=$(< /dev/urandom /usr/bin/tr -dc 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY0123456789@#$%' | /usr/bin/head -c ${1:-32})
ssh-host-config -y -c ntsec --privileged -w "$ssh_password"
mkpasswd.exe -l > /etc/passwd
mkgroup.exe -l > /etc/group
net start sshd

exit 0
