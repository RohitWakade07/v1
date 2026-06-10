#!/bin/bash
echo "=== Instructor Grader Output ==="
echo "Testing Week 4: Functions..."
if grep -qE "function [a-zA-Z_]+|[a-zA-Z_]+\(\)" /autograder/submission/main.sh; then
    echo "Function definition found! Week 4 assignment passed."
    echo "score: 100" > /autograder/results/score.txt
else
    echo "No functions found. Week 4 assignment failed."
    echo "score: 0" > /autograder/results/score.txt
fi
