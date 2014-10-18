#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "${DIR}/mjpg-streamer/mjpg-streamer"

function cleanup()
{
    test ! -z "${STREAMER}" && kill "${STREAMER}" &>/dev/null
    wait
    exit
}

trap "cleanup" SIGINT SIGHUP SIGTERM

./mjpg_streamer -i "./input_uvc.so" -o "./output_http.so -w ./www" &
STREAMER="${!}"

wait
cleanup
