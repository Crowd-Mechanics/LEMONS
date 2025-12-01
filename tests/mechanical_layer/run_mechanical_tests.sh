#!/bin/bash

set -euo pipefail

# Get the absolute path to current directory
root_dir="$(pwd)"

# Process each immediate subdirectory
for dir in test_*/ ; do
    # Remove trailing slash
    dir="${dir%/}"
    # Only process directories
    if [ -d "$dir" ]; then
        echo -e "\nProcessing directory: $dir"
        cd "$root_dir/$dir" || { echo "Cannot enter $dir"; exit 1; }

        uv run pytest ./test.py -v

        cd "$root_dir"
    fi
done

echo "All done."
