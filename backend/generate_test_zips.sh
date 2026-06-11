#!/bin/bash
set -e

# Create 100% marks zip
mkdir -p full_marks/eep-software
cd full_marks
for i in {01..12}; do
    mkdir -p eep-software/week-$i
    echo "This is week $i" > eep-software/week-$i/README.md
done
mkdir -p eep-software/notes eep-software/scripts eep-software/capstone
echo "workspace report" > eep-software/workspace-report.txt
echo "alias ll='ls -l'" > .bashrc
echo "alias la='ls -la'" >> .bashrc
zip -r ../week1_100_marks.zip .
cd ..

# Create partial marks zip
mkdir -p partial_marks/eep-software
cd partial_marks
for i in {01..06}; do
    mkdir -p eep-software/week-$i
    echo "This is week $i" > eep-software/week-$i/README.md
done
zip -r ../week1_partial_marks.zip .
cd ..

# Clean up
rm -rf full_marks partial_marks
echo "Created week1_100_marks.zip and week1_partial_marks.zip"
