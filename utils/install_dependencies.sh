#!/bin/bash

set -eu

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${THIS_DIR}/env.bash"

function download() {
    local URL="${1}"
    local FILE
    FILE="$(basename "${URL}")"
    local DIR
    DIR="$(basename "${URL}" .zip)"

    if [ ! -e "${DIR}" ]; then
        wget "${URL}"
        unzip "${FILE}"
        rm "${FILE}"
    fi
}

sudo -S true
sudo apt-get -y install streamer espeak imagemagick wget unzip

cd "${DALEK_ROOT}/html"
download https://github.com/twbs/bootstrap/releases/download/v3.3.7/bootstrap-3.3.7-dist.zip
download https://jqueryui.com/resources/download/jquery-ui-themes-1.12.1.zip
download https://jqueryui.com/resources/download/jquery-ui-1.12.1.zip
wget https://code.jquery.com/jquery-3.2.1.min.js -O jquery-3.2.1.min.js
download https://fontawesome.com/v4/assets/font-awesome-4.7.0.zip
wget https://bootswatch.com/3/darkly/bootstrap.min.css -O bootstrap.min.css
wget https://raw.githubusercontent.com/furf/jquery-ui-touch-punch/4bc009145202d9c7483ba85f3a236a8f3470354d/jquery.ui.touch-punch.min.js -O jquery.ui.touch-punch.min.js

if [ -e /etc/os-release ] && grep 'ev3dev' /etc/os-release >/dev/null; then
    source "${THIS_DIR}/pyenv.bash"
    if ! command -v pyenv >/dev/null; then
        echo 'Pyenv not installed, run setup_ev3.sh first'
        exit 1
    fi

    PYENV_VERSION="${DALEK_VIRTUALENV}" \
        CFLAGS='-march=armv5te -mcpu=arm926ej-s' \
        pyenv exec pip install \
        -r "${DALEK_ROOT}/requirements.txt" \
        --no-binary ':all:'
fi
