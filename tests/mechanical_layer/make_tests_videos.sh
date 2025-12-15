#!/usr/bin/env bash
set -euo pipefail

# Set on the shell option nullglob any glob pattern (like  *.txt) that does not match any files expands to an empty string instead of staying as the literal pattern.
shopt -s nullglob

# Ask user for ffmpeg path (allow empty to use PATH)
read -r -p "Enter the full path to ffmpeg (or leave empty to use ffmpeg from PATH): " FFMPEG_BIN

if [[ -z "${FFMPEG_BIN}" ]]; then
	FFMPEG_BIN="$(command -v ffmpeg || true)"
fi

if [[ -z "${FFMPEG_BIN}" || ! -x "${FFMPEG_BIN}" ]]; then
	echo "Error: ffmpeg not found/executable. Got: '${FFMPEG_BIN:-<empty>}'"
	exit 1
fi

# Get the absolute path to current directory
root_dir="$(pwd)"

# Ensure movies directory exists
mkdir -p "$root_dir/movies"

# Remove all .mov files in ./movies/ (does nothing if none exist)
echo "Cleaning $root_dir/movies/"
find "$root_dir/movies" -maxdepth 1 -type f -name '*.mov' -exec rm -f {} +

# Process each immediate subdirectory test_*/
for dir in test_*/; do
	dir="${dir%/}"

	if [[ ! -d "$dir" ]]; then
		continue
	fi

	echo -e "\nProcessing directory: $dir"
	uv run python "$root_dir/$dir/run_video.py" --ffmpeg="$FFMPEG_BIN"

	# Copy first .mov video from ./directory/movies/ to ./movies/
	movie_dir="$root_dir/$dir/movies"
	if [[ -d "$movie_dir" ]]; then
		mov_file="$(find "$movie_dir" -maxdepth 1 -type f -name '*.mov' -print -quit)"
		if [[ -n "$mov_file" ]]; then
			cp -p "$mov_file" "$root_dir/movies/"
			echo -e "\nCopied $(basename "$mov_file") from $movie_dir to $root_dir/movies/"
		else
			echo -e "\nNo .mov file found in $movie_dir"
		fi
	fi
done

echo -e "\nAll done."
