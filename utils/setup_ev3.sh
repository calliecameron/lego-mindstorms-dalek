#!/bin/bash

set -eu

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -e /etc/os-release ] || ! grep 'ev3dev' /etc/os-release >/dev/null; then
    echo 'Can only be run on the ev3, exiting'
    exit 1
fi

sudo -S true
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install build-essential curl git libbz2-dev libffi-dev \
    libfreetype6-dev libfribidi-dev libharfbuzz-dev libjpeg-dev liblcms2-dev \
    liblzma-dev libncursesw5-dev libopenjp2-7-dev libreadline-dev \
    libsqlite3-dev libssl-dev libtiff5-dev libwebp-dev libxcb1-dev libxml2-dev \
    libxmlsec1-dev ncurses-term python3-tk tcl8.6-dev tk-dev tk8.6-dev \
    xz-utils zlib1g-dev

source "${THIS_DIR}/env.bash"
source "${THIS_DIR}/pyenv.bash"

if ! command -v pyenv >/dev/null; then
    TMPDIR="$(mktemp -d)"
    wget -O "${TMPDIR}/pyenv-installer" 'https://raw.githubusercontent.com/pyenv/pyenv-installer/86a08ac9e38ec3a267e4b5c758891caf1233a2e4/bin/pyenv-installer'
    echo 'a1ad63c22842dce498b441551e2f83ede3e3b6ebb33f62013607bba424683191  pyenv-installer' >"${TMPDIR}/checksum"
    bash -c "cd '${TMPDIR}' && sha256sum -c checksum"
    chmod u+x "${TMPDIR}/pyenv-installer"
    "${TMPDIR}/pyenv-installer"
    rm -r "${TMPDIR}"
fi

eval "$(pyenv init --path)"

pyenv install "${DALEK_PYTHON_VERSION}"
pyenv virtualenv "${DALEK_PYTHON_VERSION}" "${DALEK_VIRTUALENV}"
