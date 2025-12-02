#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root from the script location
root_dir="$(pwd)"

build_dir="$root_dir/src/mechanical_layer/build"

# Check that build directory exists and is not empty
if [[ ! -d "$build_dir" ]]; then
    echo "Error: build directory '$build_dir' does not exist."
    exit 1
fi

if [[ -z "$(find "$build_dir" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    echo "Error: build directory '$build_dir' is empty."
    exit 1
fi

# Detect OS: macOS vs Ubuntu/Linux
os_type="unknown"
if [[ "${OSTYPE:-}" == darwin* ]]; then
    os_type="macos"
elif [[ "${OSTYPE:-}" == linux* ]]; then
    os_type="ubuntu"
fi

if [[ "$os_type" == "unknown" ]]; then
    echo "Error: unsupported or unknown OS (OSTYPE='${OSTYPE:-}')."
    exit 1
fi

echo "Detected OS: $os_type"

# Directory to process
tutorial_dir="$root_dir/tutorials/mechanical_layer"

if [[ ! -d "$tutorial_dir" ]]; then
    echo "Error: tutorials directory '$tutorial_dir' does not exist."
    exit 1
fi

# Local backup directory under tutorials/mechanical_layer
backup_dir="$tutorial_dir/.mech_backup"
echo -e "\nBacking up files to: $backup_dir"
rm -rf "$backup_dir"
mkdir -p "$backup_dir"

# Decide correct and wrong extensions depending on OS
if [[ "$os_type" == "macos" ]]; then
    correct_ext=".dylib"
    wrong_ext=".so"
else
    correct_ext=".so"
    wrong_ext=".dylib"
fi

echo "Replacing libCrowdMechanics${wrong_ext} → libCrowdMechanics${correct_ext} in $tutorial_dir"

# Find files containing libCrowdMechanics and fix extension
while IFS= read -r -d '' file; do
    # Relative path within tutorials/mechanical_layer
    rel_path="${file#$tutorial_dir/}"

    # Backup original
    mkdir -p "$backup_dir/$(dirname "$rel_path")"
    cp -- "$file" "$backup_dir/$rel_path"

    # In-place replacement; sed -i differs between macOS and Linux
    if [[ "$os_type" == "macos" ]]; then
        sed -i '' "s/libCrowdMechanics${wrong_ext}/libCrowdMechanics${correct_ext}/g" "$file"
    else
        sed -i "s/libCrowdMechanics${wrong_ext}/libCrowdMechanics${correct_ext}/g" "$file"
    fi
done < <(grep -rlZ --exclude-dir=".mech_backup" "libCrowdMechanics" "$tutorial_dir" || true)

# Prepare the environment for notebook testing: copy configuration files needed for the evacuation tutorial
cp "$root_dir/data/xml/evacuation_tutorial_initial_config_files/AgentDynamics.xml" "$tutorial_dir/dynamic/"
cp "$root_dir/data/xml/evacuation_tutorial_initial_config_files/Agents.xml" "$tutorial_dir/static/"
cp "$root_dir/data/xml/evacuation_tutorial_initial_config_files/Geometry.xml" "$tutorial_dir/static/"
cp "$root_dir/data/xml/evacuation_tutorial_initial_config_files/Materials.xml" "$tutorial_dir/static/"
cp "$root_dir/data/xml/evacuation_tutorial_initial_config_files/Parameters.xml" "$tutorial_dir/"

# Run nbmake tests on the notebooks in the tutorials folder
uv run pytest --nbmake "$tutorial_dir"

# Restore original files from backup
echo -e "\nRestoring original files from backup..."
if [[ -d "$backup_dir" ]]; then
    (cd "$backup_dir" && find . -type f -print0) | \
    while IFS= read -r -d '' bfile; do
        rel="${bfile#./}"
        dest="$tutorial_dir/$rel"
        mkdir -p "$(dirname "$dest")"
        cp -- "$backup_dir/$rel" "$dest"
    done
    rm -rf "$backup_dir"
fi

echo "All done."
