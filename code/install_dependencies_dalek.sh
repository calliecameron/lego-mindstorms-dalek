#!/bin/bash
# Install dependencies on the Dalek itself

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sudo apt-get install python-setuptools make gcc libjpeg-dev unzip python-smbus

easy_install --user python-ev3

if [ ! -e "${DIR}/mjpg-streamer" ]; then
    mkdir "${DIR}/mjpg-streamer"
    cd "${DIR}/mjpg-streamer"
    wget -O file 'https://github.com/shrkey/mjpg-streamer/raw/master/mjpg-streamer.tar.gz'
    tar -xvf file
    rm file
    cd mjpg-streamer
    make
fi
