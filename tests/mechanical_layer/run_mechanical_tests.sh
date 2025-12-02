#!/bin/bash

set -euo pipefail

# Get the absolute path to current directory
root_dir="$(pwd)"

build_dir="../../src/mechanical_layer/build"

# Check that build directory exists and is not empty
if [[ ! -d "$build_dir" ]]; then
    echo "Error: build directory '$build_dir' does not exist."
    exit 1
fi

if [ -z "$(find "$build_dir" -mindepth 1 -maxdepth 1 2>/dev/null)" ]; then
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

# Directories to process
search_dirs=(
    "./"
    "../../tutorials/mechanical_layer"
)

# Temporary backup directory
backup_dir="$(mktemp -d)"
echo -e "\nBacking up files to: $backup_dir"

# Decide correct and wrong extensions depending on OS
if [[ "$os_type" == "macos" ]]; then
    correct_ext=".dylib"
    wrong_ext=".so"
else
    correct_ext=".so"
    wrong_ext=".dylib"
fi

# Find files containing libCrowdMechanics and fix extension
for rel_dir in "${search_dirs[@]}"; do
    dir_path="$root_dir/$rel_dir"
    if [[ ! -d "$dir_path" ]]; then
        echo "Skipping missing directory: $dir_path"
        continue
    fi

    # Only consider regular files that mention libCrowdMechanics
    while IFS= read -r -d '' file; do
        # Backup original file (preserving relative path)
        rel_path="${file#$root_dir/}"
        backup_path="$backup_dir/$rel_path"
        mkdir -p "$(dirname "$backup_path")"
        cp -- "$file" "$backup_path"

        # Replace wrong extension with correct one
        sed -i "s/libCrowdMechanics${wrong_ext}/libCrowdMechanics${correct_ext}/g" "$file"
    done < <(grep -rlZ "libCrowdMechanics" "$dir_path" || true)
done

# Process each immediate subdirectory test_*/
for dir in test_*/ ; do
    dir="${dir%/}"
    if [ -d "$dir" ]; then
        echo -e "\nProcessing directory: $dir"
        cd "$root_dir/$dir" || { echo "Cannot enter $dir"; exit 1; }

        uv run pytest ./test.py -v

        cd "$root_dir"
    fi
done

# Restore original files
echo "Restoring original files..."
for rel_dir in "${search_dirs[@]}"; do
    src_dir="$backup_dir/$rel_dir"
    if [[ -d "$src_dir" ]]; then
        (cd "$backup_dir" && find "$rel_dir" -type f -print0) | \
        while IFS= read -r -d '' bfile; do
            orig_path="$root_dir/$bfile"
            mkdir -p "$(dirname "$orig_path")"
            cp -- "$backup_dir/$bfile" "$orig_path"
        done
    fi
done

rm -rf "$backup_dir"

echo -e "\nAll done."
