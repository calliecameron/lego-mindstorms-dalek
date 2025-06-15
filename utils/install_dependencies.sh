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
download https://github.com/twbs/bootstrap/releases/download/v5.3.6/bootstrap-5.3.6-dist.zip
download https://jqueryui.com/resources/download/jquery-ui-themes-1.14.1.zip
download https://jqueryui.com/resources/download/jquery-ui-1.14.1.zip
wget https://code.jquery.com/jquery-3.7.1.min.js -O jquery-3.7.1.min.js
download https://use.fontawesome.com/releases/v6.7.2/fontawesome-free-6.7.2-web.zip
wget https://bootswatch.com/5/darkly/bootstrap.min.css -O bootstrap.min.css
wget https://raw.githubusercontent.com/RWAP/jquery-ui-touch-punch/54639b5f9cd58d896f3ab2f83759c24acb68d9d4/jquery.ui.touch-punch.js -O jquery.ui.touch-punch.js

if [ -e /etc/os-release ] && grep 'ev3dev' /etc/os-release >/dev/null; then
    source "${THIS_DIR}/pyenv.bash"
    if ! command -v pyenv >/dev/null; then
        echo 'Pyenv not installed, run setup_ev3.sh first'
        exit 1
    fi

    PYENV_VERSION="${DALEK_VIRTUALENV}" \
        CFLAGS='-march=armv5te -mcpu=arm926ej-s' \
        pyenv exec pip --no-cache-dir install \
        -r "${DALEK_ROOT}/requirements.txt" \
        --no-binary ':all:'
fi
