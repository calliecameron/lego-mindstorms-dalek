#!/bin/bash
# Install dependencies on the Dalek itself

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sudo apt-get install python-setuptools make gcc libjpeg-dev unzip

easy_install --user python-ev3

if [ ! -e "${DIR}/mastermind" ]; then
    mkdir "${DIR}/mastermind"
    cd "${DIR}/mastermind"
    wget -O zip 'http://www.geometrian.com/data/programming/projects/Mastermind%20Networking%20Library/4.1.3/Mastermind%204.1.3.zip'
    unzip zip
    rm zip
fi

if [ ! -e "${DIR}/mjpg-streamer" ]; then
    mkdir "${DIR}/mjpg-streamer"
    cd "${DIR}/mjpg-streamer"
    wget -O file 'https://github.com/shrkey/mjpg-streamer/raw/master/mjpg-streamer.tar.gz'
    tar -xvf file
    rm file
    cd mjpg-streamer
    make
fi

echo "Add ${DIR}/mastermind/4.1.3 to your PYTHONPATH"
