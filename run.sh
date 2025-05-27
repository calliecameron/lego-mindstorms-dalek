#!/bin/bash
# Takes the path to a sounds folder as argument; will look in ~/sounds if none
# specified.

set -eu

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${THIS_DIR}/utils/env.bash"

if [ -n "${1:-}" ]; then
    SOUNDS_DIR="$(readlink -f "${1}")"
else
    SOUNDS_DIR="${HOME}/sounds"
fi

if [ -e /etc/os-release ] && grep 'ev3dev' /etc/os-release >/dev/null; then
    source "${THIS_DIR}/utils/pyenv.bash"
    if ! command -v pyenv >/dev/null; then
        echo 'Pyenv not installed, run setup_ev3.sh first'
        exit 1
    fi

    function run-python() {
        PYENV_VERSION="${DALEK_VIRTUALENV}" pyenv exec python3 "${@}"
    }
else
    function run-python() {
        python3 "${@}"
    }
fi

WEBSOCKET=''
HTTP=''

function cleanup() {
    # shellcheck disable=SC2015
    test -n "${WEBSOCKET}" && kill "${WEBSOCKET}" &>/dev/null || true
    # shellcheck disable=SC2015
    test -n "${HTTP}" && kill "${HTTP}" &>/dev/null || true
    wait
    exit 0
}

trap cleanup SIGINT SIGTERM

echo 'LAUNCHER: starting web server...'
run-python -m http.server --directory "${THIS_DIR}/html" 12345 &
HTTP="${!}"
echo 'LAUNCHER: started web server'

echo 'LAUNCHER: starting dalek...'
run-python -m dalek \
    "${SOUNDS_DIR}" \
    "${THIS_DIR}/utils/text_to_speech.sh" \
    "${THIS_DIR}/utils/take_picture.sh" \
    "${THIS_DIR}/picture.jpeg" &
WEBSOCKET="${!}"
echo 'LAUNCHER: started dalek'

wait "${WEBSOCKET}"
cleanup
