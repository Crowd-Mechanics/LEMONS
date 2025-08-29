#!/bin/bash

# Exit immediately on errors and unset variables
set -e

# Save the original directory and move to docs/
ORIG_DIR=$(pwd)
cd docs || { echo "Error: 'docs' directory not found"; exit 1; }

# Path to your Doxygen config file (now relative to docs/)
DOXYFILE="Doxyfile"

# Temporary file for capturing warnings
WARNINGS_FILE=$(mktemp)

# Run Doxygen from the docs/ directory
doxygen "$DOXYFILE" 2> "$WARNINGS_FILE"

# Process warnings and return to original directory
if grep -q "warning:" "$WARNINGS_FILE"; then
    echo "Doxygen warnings/errors detected:"
    cat "$WARNINGS_FILE"
    rm "$WARNINGS_FILE"
    cd "$ORIG_DIR" || exit 1  # Return to original directory before exiting
    exit 1
else
    echo "Doxygen check passed: No warnings found."
    rm "$WARNINGS_FILE"
    cd "$ORIG_DIR" || exit 1  # Return to original directory
    exit 0
fi
