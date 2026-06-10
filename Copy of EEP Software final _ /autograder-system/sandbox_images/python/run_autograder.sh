#!/bin/sh

# The entrypoint for the grading container
# We invoke the python grader script which handles pytest and results parsing
python /autograder/grader.py

# Exit with the status of the grader
exit $?
