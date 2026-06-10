#!/bin/bash
echo "=== Instructor Grader Output ==="
echo "Testing Week 3: Conditionals..."
if grep -q "if " /autograder/submission/main.sh || grep -q "case " /autograder/submission/main.sh; then
    echo "Conditional logic found! Week 3 assignment passed."
    echo "score: 100" > /autograder/results/score.txt
else
    echo "No conditionals found. Week 3 assignment failed."
    echo "score: 0" > /autograder/results/score.txt
fi
