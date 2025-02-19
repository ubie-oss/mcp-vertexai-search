# Constants
SCRIPT_FILE="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "${SCRIPT_FILE}")"
MODULE_DIR="$(dirname "${SCRIPT_DIR}")"

# Arguments
deps="production"
use_venv=false
while (($# > 0)); do
	if [[ $1 == "--use-venv" ]]; then
		use_venv=true
		shift 1
	elif [[ $1 == "--deps" ]]; then
		if [[ $2 != "production" && $2 != "development" ]]; then
			echo "Error: deps must be one of 'production' or 'development'"
			exit 1
		fi
		deps="$2"
		shift 2
	else
		echo "Unknown argument: $1"
		exit 1
	fi
done

# Change to the module directory
cd "${MODULE_DIR}"

# Install uv and dependencies
pip install --force-reinstall -r "${MODULE_DIR}/requirements.setup.txt"

UV_PIP_OPTIONS=("--force-reinstall")
if [[ ${use_venv} == true ]]; then
	# Create virtual environment
	uv venv
	# Activate virtual environment
	if [[ -f .venv/bin/activate ]]; then
		# shellcheck disable=SC1091
		source .venv/bin/activate
	else
		echo "Error: .venv/bin/activate not found"
		exit 1
	fi
else
	UV_PIP_OPTIONS+=("--system")
fi

# Install package and dependencies
if [[ ${deps} == "production" ]]; then
	uv pip install "${UV_PIP_OPTIONS[@]}" -e "."
else
	uv pip install "${UV_PIP_OPTIONS[@]}" -e ".[dev,test]"
fi
