set -Eo pipefail
set -x

# Constants
SCRIPT_FILE="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "${SCRIPT_FILE}")"
MODULE_DIR="$(dirname "${SCRIPT_DIR}")"

cd "${MODULE_DIR}" || exit

# Arguments
target=${1:?"target is not set"}

# Ensure uv is installed
pip install uv

# Build the package first
uv build

# Publish to the specified target
if [[ ${target} == "pypi" ]]; then
	uv publish
elif [[ ${target} == "testpypi" ]]; then
	uv publish --publish-url "https://test.pypi.org/legacy/"
else
	echo "No such target ${target}"
	exit 1
fi
