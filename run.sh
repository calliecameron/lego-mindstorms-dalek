#!/bin/bash
# Run this script on the Dalek to make it take commands from a computer.
# Takes the path to a sounds folder as argument; will look in ~/sounds
# if none specified.

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -n "${1}" ]; then
    SOUNDS_DIR="$(readlink -f "${1}")"
else
    SOUNDS_DIR="${HOME}/sounds"
fi

WEBSOCKET=''
HTTP=''

function cleanup() {
    test ! -z "${WEBSOCKET}" && kill "${WEBSOCKET}" &>/dev/null
    test ! -z "${HTTP}" && kill "${HTTP}" &>/dev/null
    wait
    exit 0
}

trap cleanup SIGINT SIGTERM

cd "${THIS_DIR}/html" || exit 1
python -m SimpleHTTPServer 12345 &
HTTP="${!}"
cd "${THIS_DIR}/internal" || exit 1
python "${THIS_DIR}/internal/remote_receiver.py" \
    "${SOUNDS_DIR}" \
    "${THIS_DIR}/internal/text_to_speech.sh" \
    "${THIS_DIR}/internal/snapshot.sh" &
WEBSOCKET="${!}"
wait "${WEBSOCKET}"
cleanup
