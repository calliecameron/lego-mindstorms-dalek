#!/bin/bash
# Setup the LEDs ready for the main code to use

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODE_FILE='/sys/bus/legoev3/devices/outC/mode'

if [ "$(cat "${MODE_FILE}")" != 'rcx-led' ]; then
    echo rcx-led | sudo tee /sys/bus/legoev3/devices/outC/mode &>/dev/null
fi

function cleanup()
{
    test ! -z "${REAL_PID}" && kill "${REAL_PID}" &>/dev/null
    wait
    exit
}

trap "cleanup" SIGINT SIGHUP SIGTERM

python "${DIR}/remote_receiver.py" "${HOME}/sounds" &
REAL_PID="${!}"

wait
cleanup
