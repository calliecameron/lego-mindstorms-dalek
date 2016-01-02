#!/bin/bash
# Run this script on your computer to control the Dalek. Takes the IP address
# of the Dalek as an argument, or queries for it if none given. 'run_on_dalek.sh'
# must already be running on the Dalek.

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LAST_IP_FILE="${THIS_DIR}/last-ip-address.txt"

if [ -e "${LAST_IP_FILE}" ]; then
    LAST_IP_ADDR="$(cat "${LAST_IP_FILE}")"
else
    LAST_IP_ADDR=''
fi

if [ ! -z "${1}" ]; then
    ADDR="${1}"
else
    ADDR="$(zenity --entry --title=Dalek "--entry-text=${LAST_IP_ADDR}" "--text=Enter the Dalek's IP address:" "--window-icon=${THIS_DIR}/internal/dalek.ico")"
    if [ -z "${ADDR}" ]; then
        zenity --error --title=Dalek "--text=No address entered; quitting." "--window-icon=${THIS_DIR}/internal/dalek.ico"
        exit 1
    else
        echo "${ADDR}" > "${LAST_IP_FILE}"
    fi
fi

cd "${THIS_DIR}/internal"
OUTPUT="$(python "${THIS_DIR}/internal/control_remote.py" "${ADDR}" "${THIS_DIR}/last-photo.jpg" 2>&1)"
if [ ! -z "${OUTPUT}" ]; then
    echo "${OUTPUT}"
    zenity --error --title=Dalek "--text=${OUTPUT}" "--window-icon=${THIS_DIR}/internal/dalek.ico"
fi
