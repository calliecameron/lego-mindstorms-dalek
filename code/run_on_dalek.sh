#!/bin/bash
# Run this script on the Dalek to make it take commands from a computer.
# Takes the path to a sounds folder as argument; will look in ~/sounds
# if none specified.

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -z "${1}" ]; then
    SOUNDS_DIR="$(readlink -f "${1}")"
else
    SOUNDS_DIR="${HOME}/sounds"
fi

cd "${THIS_DIR}/internal"
exec python "${THIS_DIR}/internal/remote_receiver.py" "${SOUNDS_DIR}"
