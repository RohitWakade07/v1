#!/bin/bash
echo "=== Instructor Grader Output ==="
echo "Testing Week 2: Loops..."
if grep -q "for" /autograder/submission/main.sh || grep -q "while" /autograder/submission/main.sh; then
    echo "Loop found! Week 2 assignment passed."
    echo "score: 100" > /autograder/results/score.txt
else
    echo "No loop found. Week 2 assignment failed."
    echo "score: 0" > /autograder/results/score.txt
fi
