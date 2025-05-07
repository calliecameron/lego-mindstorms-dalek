#!/bin/bash
# Because the Dalek's camera is on its side, we rotate the image after capturing
# it.

set -eu

function usage() {
    echo "Usage: $(basename "${0}") out_file"
    exit 1
}

test -z "${1:-}" && usage
OUT_FILE="${1}"
TEMP_FILE="${OUT_FILE}.tmp"

streamer -s 800x600 -o "${OUT_FILE}"
mv "${OUT_FILE}" "${TEMP_FILE}"
convert "${TEMP_FILE}" -rotate 270 "${OUT_FILE}"
rm "${TEMP_FILE}"
