#!/bin/bash

set -eu

git ls-files | LC_ALL=C sort | while read -r line; do
    if ! file -bi "${line}" | grep 'charset=binary' >/dev/null; then
        HEAD="$(head -n 1 "${line}")"
        if [[ "${line}" == *'.sh' ]] || [[ "${line}" == *'.bash' ]] ||
            [ "${HEAD}" = '#!/bin/sh' ] || [ "${HEAD}" = '#!/bin/bash' ]; then
            echo "${line}"
        fi
    fi
done
