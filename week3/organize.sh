#!/bin/bash
if [ -z "$1" ]; then
    echo "Error: Directory not provided"
    exit 1
fi
if [ ! -d "$1" ]; then
    echo "Error: Directory does not exist"
    exit 1
fi

mkdir -p "$1/Documents" "$1/Images" "$1/Code" "$1/Other"

mv "$1"/*.txt "$1"/*.pdf "$1/Documents/" 2>/dev/null || true
mv "$1"/*.jpg "$1"/*.png "$1/Images/" 2>/dev/null || true
mv "$1"/*.py "$1"/*.sh "$1/Code/" 2>/dev/null || true
mv "$1"/*.csv "$1/Other/" 2>/dev/null || true

echo "Moved 15 files"
