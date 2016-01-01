#!/bin/bash
# Run this script on your computer to control the Dalek. Takes the IP address
# of the Dalek as an argument. 'run_on_dalek.sh' must already be running on
# the Dalek.

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function usage() {
    echo "Usage: $(basename "${0}") dalek-ip-address"
    exit 1
}

test -z "${1}" && usage

cd "${THIS_DIR}/internal"
exec python "${THIS_DIR}/internal/control_remote.py" "${1}" "${THIS_DIR}/last-photo.jpg"
