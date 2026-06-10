#!/bin/bash
# organize.sh — File Organizer
# Week 3 EEP Software Assignment
# Takes a directory path, sorts files into Documents/, Images/, Code/, Other/

# Validate input
if [[ $# -ne 1 ]]; then
    echo "Usage: organize.sh <directory_path>"
    exit 1
fi

TARGET="$1"

if [[ ! -d "$TARGET" ]]; then
    echo "Error: '$TARGET' is not a valid directory."
    exit 1
fi

# Create sub-folders
mkdir -p "$TARGET/Documents" "$TARGET/Images" "$TARGET/Code" "$TARGET/Other"

# Counters
docs=0
imgs=0
code=0
other=0

# Sort files by extension
for file in "$TARGET"/*; do
    # Skip if not a regular file (skip directories)
    if [[ ! -f "$file" ]]; then
        continue
    fi

    # Get the filename (without path)
    filename="$(basename "$file")"

    # Skip files already in sub-folders (shouldn't happen but safety check)
    case "$filename" in
        Documents|Images|Code|Other) continue ;;
    esac

    # Get extension (lowercase)
    ext="${filename##*.}"
    ext="$(echo "$ext" | tr '[:upper:]' '[:lower:]')"

    # Sort based on extension
    if [[ "$ext" == "txt" || "$ext" == "pdf" || "$ext" == "doc" || "$ext" == "docx" ]]; then
        mv "$file" "$TARGET/Documents/"
        ((docs++))
    elif [[ "$ext" == "jpg" || "$ext" == "jpeg" || "$ext" == "png" || "$ext" == "gif" || "$ext" == "bmp" ]]; then
        mv "$file" "$TARGET/Images/"
        ((imgs++))
    elif [[ "$ext" == "py" || "$ext" == "sh" || "$ext" == "js" || "$ext" == "c" || "$ext" == "cpp" ]]; then
        mv "$file" "$TARGET/Code/"
        ((code++))
    else
        mv "$file" "$TARGET/Other/"
        ((other++))
    fi
done

# Print summary
echo "=== File Organization Summary ==="
echo "Documents: $docs files"
echo "Images:    $imgs files"
echo "Code:      $code files"
echo "Other:     $other files"
echo "Total:     $((docs + imgs + code + other)) files moved"
