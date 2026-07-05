#!/bin/bash
# Organizes files in a directory by extension

if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>" >&2
    exit 1
fi

DIR="$1"

if [ ! -d "$DIR" ]; then
    echo "Error: '$DIR' is not a directory." >&2
    exit 1
fi

mkdir -p "$DIR/Documents" "$DIR/Images" "$DIR/Code" "$DIR/Other"

docs=0; imgs=0; code=0; other=0

for file in "$DIR"/*; do
    [ -f "$file" ] || continue
    ext="${file##*.}"
    case "${ext,,}" in
        txt|pdf)  mv "$file" "$DIR/Documents/"; ((docs++)) ;;
        jpg|png)  mv "$file" "$DIR/Images/";    ((imgs++)) ;;
        py|sh)    mv "$file" "$DIR/Code/";      ((code++)) ;;
        *)        mv "$file" "$DIR/Other/";     ((other++)) ;;
    esac
done

echo "Documents: $docs files"
echo "Images: $imgs files"
echo "Code: $code files"
echo "Other: $other files"
