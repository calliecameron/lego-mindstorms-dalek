#!/bin/bash
# Setup the LEDs ready for the main code to use

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo rcx-led | sudo tee /sys/bus/legoev3/devices/outC/mode &>/dev/null

function cleanup()
{
    test ! -z "${REAL_PID}" && kill "${REAL_PID}" &>/dev/null
    wait
    exit
}

python "${DIR}/remote_receiver.py" "${HOME}/sounds" &
REAL_PID="${!}"

wait
cleanup
