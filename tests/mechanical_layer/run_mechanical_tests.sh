#!/usr/bin/env bash
set -euo pipefail

# Get the absolute path to current directory
root_dir="$(pwd)"

build_dir="../../src/mechanical_layer/build"

# Check that build directory exists and is not empty
if [[ ! -d "$build_dir" ]]; then
	echo "Error: build directory '$build_dir' does not exist."
	exit 1
fi

# Portable "is directory empty?" check (works on macOS + Linux)
if [[ -z "$(ls -A "$build_dir" 2>/dev/null || true)" ]]; then
	echo "Error: build directory '$build_dir' is empty."
	exit 1
fi

# Detect OS: macOS vs Linux
os_type="unknown"
case "$(uname -s)" in
Darwin) os_type="macos" ;;
Linux) os_type="linux" ;;
esac

if [[ "$os_type" == "unknown" ]]; then
	echo "Error: unsupported or unknown OS (uname -s = '$(uname -s)')."
	exit 1
fi

echo "Detected OS: $os_type"

# Portable in-place sed that works both on macOS and Linux:
sed_inplace() {
	local expr="$1"
	local file="$2"

	if [[ "$os_type" == "macos" ]]; then
		sed -i '' -e "$expr" "$file"
	else
		sed -i -e "$expr" "$file"
	fi
}

# Directories to process
search_dirs=("./")

# Temporary backup directory
backup_dir="$root_dir/.mech_backup"
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

# Find files containing libCrowdMechanics and fix extension
for rel_dir in "${search_dirs[@]}"; do
	dir_path="$root_dir/$rel_dir"
	if [[ ! -d "$dir_path" ]]; then
		echo "Skipping missing directory: $dir_path"
		continue
	fi

	# Iterate over regular files robustly (handles spaces/newlines)
	while IFS= read -r -d '' file; do
		# Only modify files that actually mention libCrowdMechanics
		if ! grep -q "libCrowdMechanics" "$file" 2>/dev/null; then
			continue
		fi

		# Backup original file (preserving relative path)
		rel_path="${file#$root_dir/}"
		backup_path="$backup_dir/$rel_path"
		mkdir -p "$(dirname "$backup_path")"
		cp -p "$file" "$backup_path"

		# Replace wrong extension with correct one
		sed_inplace "s/libCrowdMechanics${wrong_ext}/libCrowdMechanics${correct_ext}/g" "$file"
	done < <(find "$dir_path" -type f -print0)
done

# Process each immediate subdirectory test_*/
for dir in test_*/; do
	dir="${dir%/}"
	if [[ -d "$dir" ]]; then
		echo -e "\nProcessing directory: $dir"
		cd "$root_dir/$dir" || {
			echo "Cannot enter $dir"
			exit 1
		}

		uv run pytest ./test.py -v

		cd "$root_dir"
	fi
done

# Restore original files
echo "Restoring original files..."
for rel_dir in "${search_dirs[@]}"; do
	src_dir="$backup_dir/$rel_dir"
	if [[ -d "$src_dir" ]]; then
		while IFS= read -r -d '' bfile; do
			orig_path="$root_dir/$bfile"
			mkdir -p "$(dirname "$orig_path")"
			cp -p "$backup_dir/$bfile" "$orig_path"
		done < <(cd "$backup_dir" && find "$rel_dir" -type f -print0)
	fi
done

rm -rf "$backup_dir"

echo -e "\nAll done."
