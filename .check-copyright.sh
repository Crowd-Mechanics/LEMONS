#!/usr/bin/env bash
set -euo pipefail

# Directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Header templates (adjust paths if you move them)
PY_HEADER_FILE="$SCRIPT_DIR/LICENSE_PY_HEADER.txt"
CPP_HEADER_FILE="$SCRIPT_DIR/LICENSE_CPP_HEADER.txt"

# Verify that header template files exist
if [[ ! -f "$PY_HEADER_FILE" ]]; then
    echo "Missing Python license header template: $PY_HEADER_FILE"
    exit 1
fi
if [[ ! -f "$CPP_HEADER_FILE" ]]; then
    echo "Missing C/C++ license header template: $CPP_HEADER_FILE"
    exit 1
fi

# Precompute header line counts
PY_HEADER_LINES=$(wc -l < "$PY_HEADER_FILE")
CPP_HEADER_LINES=$(wc -l < "$CPP_HEADER_FILE")

echo "Checking license headers..."
echo "  Python header: $PY_HEADER_LINES lines"
echo "  C/C++ header:  $CPP_HEADER_LINES lines"

failed=0

check_file() {
    local file="$1"
    local header_file="$2"
    local header_lines="$3"
    local start_line="$4"   # line number where the header should start in the file

    # Extract slice [start_line, start_line+header_lines-1]
    local header_slice=$(tail -n +"$start_line" "$file" | head -n "$header_lines")

    # local diff_output
    if ! diff_output=$(diff -u "$header_file" - <<<"$header_slice"); then
        echo "HEADER MISMATCH: $file"
        printf '%s\n' "$diff_output"
        failed=1
    fi
}

########################################
# Python files (in src + tests, recursively)
########################################

for f in $(find ./src ./tests -type f -name '*.py'); do
    # Skip __init__.py
    if [[ "$(basename "$f")" == "__init__.py" ]]; then
        continue
    fi

    # Compute start line for the license header: line after module docstring
    start_line=$(uv run python - <<'PY' "$f"
import ast, sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as fh:
    src = fh.read()

module = ast.parse(src)

# Default: header from line 1 if no module docstring
start = 1

if module.body and isinstance(module.body[0], ast.Expr):
    value = module.body[0].value
    # Python 3.8+: ast.Constant for strings; older: ast.Str
    if (isinstance(value, ast.Constant) and isinstance(value.value, str)) or isinstance(value, ast.Str):
        node = module.body[0]
        end = getattr(node, "end_lineno", None)
        if end is None:
            # Fallback if end_lineno not available: approximate from docstring length
            doc = ast.get_docstring(module, clean=False)
            if doc is not None:
                lines = doc.count("\n")
                end = node.lineno + lines
        if end is not None:
            start = end + 1

print(start)
PY
)
    start_line=$((start_line + 1))
    # Display file that being checked
    # echo "Checking $f (header starts at line $start_line)"
    # Python header starts at line 3
    check_file "$f" "$PY_HEADER_FILE" "$PY_HEADER_LINES" "$start_line"
done

########################################
# C++ / header files (in src only, recursively)
########################################

for f in $(find ./src -type f \( -name '*.cpp' -o -name '*.h' \)); do
    # Skip 3rd party code
    if [[ "$f" == *3rdparty* ]]; then
        continue
    fi
    # Skip build files
    if [[ "$f" == *build* ]]; then
        continue
    fi

    # C/C++ header starts at line 1
    check_file "$f" "$CPP_HEADER_FILE" "$CPP_HEADER_LINES" 1
done

if (( failed == 0 )); then
    echo
    echo "All checked files have the correct license headers."
else
    echo
    echo "Some files are missing or have incorrect license headers."
    exit 1
fi
