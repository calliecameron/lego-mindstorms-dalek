export PYENV_ROOT="${HOME}/.pyenv"
export PATH="${PYENV_ROOT}/bin:${PATH}"
DALEK_ROOT="$(readlink -f "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/..")"
export DALEK_ROOT
DALEK_PYTHON_VERSION="$(cat "${DALEK_ROOT}/.python-version")"
export DALEK_PYTHON_VERSION
export DALEK_VIRTUALENV='dalek'
