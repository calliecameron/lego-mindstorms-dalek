#!/bin/bash
# Run this script once on the Dalek itself; it installs all the necessary
# software.

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function download() {
    URL="${1}"
    FILE="$(basename "${URL}")"
    DIR="$(basename "${URL}" .zip)"

    if [ ! -e "${DIR}" ]; then
        wget "${URL}" &&
        unzip "${FILE}" &&
        rm "${FILE}" || return 1
    fi
}

sudo apt-get -y install streamer espeak imagemagick &&

cd "${THIS_DIR}/html" &&
download https://github.com/twbs/bootstrap/releases/download/v3.3.7/bootstrap-3.3.7-dist.zip &&
download https://jqueryui.com/resources/download/jquery-ui-themes-1.12.1.zip &&
download https://jqueryui.com/resources/download/jquery-ui-1.12.1.zip &&
wget https://code.jquery.com/jquery-3.2.1.min.js -O jquery-3.2.1.min.js &&
download http://fontawesome.io/assets/font-awesome-4.7.0.zip &&
wget https://bootswatch.com/darkly/bootstrap.min.css -O bootstrap.min.css
