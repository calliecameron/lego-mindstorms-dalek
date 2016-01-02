#!/bin/bash
# Run this script on your computer to control the Dalek. Takes the IP address
# of the Dalek as an argument, or queries for it if none given. 'run_on_dalek.sh'
# must already be running on the Dalek.

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -z "${1}" ]; then
    ADDR="${1}"
else
    ADDR="$(zenity --entry --title=Dalek "--text=Enter the Dalek's IP address:" "--window-icon=${THIS_DIR}/internal/dalek.ico")"
    if [ -z "${ADDR}" ]; then
        zenity --error --title=Dalek "--text=No address entered; quitting." "--window-icon=${THIS_DIR}/internal/dalek.ico"
        exit 1
    fi
fi

cd "${THIS_DIR}/internal"
OUTPUT="$(python "${THIS_DIR}/internal/control_remote.py" "${ADDR}" "${THIS_DIR}/last-photo.jpg" 2>&1)"
if [ ! -z "${OUTPUT}" ]; then
    echo "${OUTPUT}"
    zenity --error --title=Dalek "--text=${OUTPUT}" "--window-icon=${THIS_DIR}/internal/dalek.ico"
fi
