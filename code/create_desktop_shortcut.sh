#!/bin/bash

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

TMPFILE='/tmp/dalek.desktop'
sed "s|@@@@@1@@@@@|${THIS_DIR}/run_on_computer.sh|g" < "${THIS_DIR}/internal/dalek.desktop" | sed "s|@@@@@2@@@@@|${THIS_DIR}/internal/dalek.ico|g" > "${TMPFILE}" &&
xdg-desktop-icon install --novendor "${TMPFILE}"
