#! /bin/bash


. /lib/lsb/init-functions
set -e
PATH=/sbin:/bin:/usr/sbin:/usr/bin

log_daemon_msg "Starting dinghangspot\n"
source /home/pi/.virtualenvs/cv/bin/activate
sleep 5   # cannot find a way to get it to start after socketports are ready
log_daemon_msg "calling hangtrackingscript"
python /home/pi/hangtrackingscript.py

