#!/bin/bash
# Install dependencies on the Dalek itself

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sudo apt-get install python-setuptools

easy_install --user python-ev3

if [ ! -e "${DIR}/mastermind" ]; then
    mkdir "${DIR}/mastermind"
    cd "${DIR}/mastermind"
    wget -O zip 'http://www.geometrian.com/data/programming/projects/Mastermind%20Networking%20Library/4.1.3/Mastermind%204.1.3.zip'
    unzip zip
    rm zip
fi

echo "Add ${DIR}/mastermind/4.1.3 to your PYTHONPATH"
