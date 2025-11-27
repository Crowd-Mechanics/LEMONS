#!/bin/bash

set -euo pipefail

# Choose ffmpeg binary path:
# - If FFMPEG_BIN is set in the environment, use that.
# - Otherwise, default to "ffmpeg" (must be on PATH).
FFMPEG_BIN="${FFMPEG_BIN:-/Users/oscardufour/ffmpeg_bin/ffmpeg}"

# Check that ffmpeg is available
if ! "$FFMPEG_BIN" -version >/dev/null 2>&1; then
    echo "Error: ffmpeg executable '$FFMPEG_BIN' not found in PATH."
    echo "Install ffmpeg or set FFMPEG_BIN=/full/path/to/ffmpeg before running this script."
    exit 1
fi

# Get the absolute path to current directory
root_dir="$(pwd)"

# Process each immediate subdirectory
for dir in test_*/ ; do
    # Remove trailing slash
    dir="${dir%/}"
    # Only process directories
    if [ -d "$dir" ]; then
        echo "Processing directory: $dir"
        cd "$root_dir/$dir" || { echo "Cannot enter $dir"; exit 1; }

        uv run python ./run_simulation.py
        uv run python ./run_video.py --ffmpeg="$FFMPEG_BIN"

        cd "$root_dir"
    fi
done

# Ensure movies directory exists
mkdir -p "$root_dir/movies"

# Remove all files in ./movies/
echo "Cleaning $root_dir/movies/"
rm -f "$root_dir/movies/"*.mov

# Copy .mov video from each ./directory/movies/ to ./movies/
for dir in test_*/ ; do
    dir="${dir%/}"
    movie_dir="$root_dir/$dir/movies"
    if [ -d "$movie_dir" ]; then
        # Find first .mov file in the movie_dir
        mov_file=$(find "$movie_dir" -maxdepth 1 -type f -name '*.mov' | head -n 1)
        if [ -n "$mov_file" ]; then
            cp "$mov_file" "$root_dir/movies/"
            echo "Copied $(basename "$mov_file") from $dir/movies/ to movies/"
        else
            echo "No .mov file found in $dir/movie/"
        fi
    fi
done

echo "All done."
