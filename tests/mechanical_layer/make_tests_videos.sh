#!/bin/bash

set -euo pipefail

# Ask user for ffmpeg path
read -p "Enter the full path to ffmpeg: " FFMPEG_BIN

# Get the absolute path to current directory
root_dir="$(pwd)"

# Ensure movies directory exists
mkdir -p "$root_dir/movies"

# Remove all files in ./movies/
echo "Cleaning $root_dir/movies/"
rm -f "$root_dir/movies/"*.mov

# Process each immediate subdirectory
for dir in test_*/ ; do
    # Remove trailing slash
    dir="${dir%/}"
    # Make the videos
    if [ -d "$dir" ]; then
        echo -e "\nProcessing directory: $dir"
        uv run python $root_dir/$dir/run_video.py --ffmpeg="$FFMPEG_BIN"
    fi
    # Copy .mov video from each ./directory/movies/ to ./movies/
    movie_dir="$root_dir/$dir/movies"
    if [ -d "$movie_dir" ]; then
        # Find first .mov file in the movie_dir
        mov_file=$(find "$movie_dir" -maxdepth 1 -type f -name '*.mov' | head -n 1)
        if [ -n "$mov_file" ]; then
            cp "$mov_file" "$root_dir/movies/"
            echo -e "\nCopied $(basename "$mov_file") from $root_dir/$dir/movies/ to $root_dir/movies/"
        else
            echo -e "\nNo .mov file found in $root_dir/$dir/movies/"
        fi
    fi
done

echo -e "\nAll done."
