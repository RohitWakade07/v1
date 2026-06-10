#!/bin/bash

# Record start time in milliseconds
START_TIME=$(date +%s%3N)

# Initialize output
SCORE=0
STATUS="failed"
FEEDBACK=""
TESTS="[]"

# We assume the user's code is mounted at /autograder/submission/main.sh
# Because the Celery worker currently creates "main.py" by default unless we adjust it.
# Wait, actually the workspace manager writes the code to a file based on language extension.
# Let's assume it writes to /autograder/submission/main.sh

if [ ! -f /autograder/submission/main.sh ]; then
    FEEDBACK="Error: Submission file not found."
else
    # Execute the script
    # We will run it in a subshell and capture stdout and stderr
    # We apply a timeout of 5 seconds
    
    OUTPUT=$(timeout 5s bash /autograder/submission/main.sh 2>&1)
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 124 ]; then
        FEEDBACK="Execution Timeout: Script took longer than 5 seconds."
        STATUS="failed"
        SCORE=0
    elif [ $EXIT_CODE -eq 0 ]; then
        STATUS="completed"
        SCORE=100
        FEEDBACK="Command executed successfully.\nOutput:\n$OUTPUT"
        
        # Build test list with jq
        TESTS=$(jq -n --arg msg "Exited with code 0" '[{"name": "Execution Check", "passed": true, "message": $msg}]')
    else
        STATUS="failed"
        SCORE=0
        FEEDBACK="Command failed with exit code $EXIT_CODE.\nOutput:\n$OUTPUT"
        
        TESTS=$(jq -n --arg msg "Exited with code $EXIT_CODE" '[{"name": "Execution Check", "passed": false, "message": $msg}]')
    fi
fi

# Calculate execution time
END_TIME=$(date +%s%3N)
EXECUTION_TIME_MS=$((END_TIME - START_TIME))

# Truncate feedback if it's too long
FEEDBACK=$(echo "$FEEDBACK" | head -c 5000)

# Generate results.json using jq
jq -n \
  --argjson score "$SCORE" \
  --arg status "$STATUS" \
  --arg feedback "$FEEDBACK" \
  --argjson tests "$TESTS" \
  --argjson time_ms "$EXECUTION_TIME_MS" \
  '{score: $score, status: $status, feedback: $feedback, tests: $tests, execution_time_ms: $time_ms}' > /autograder/results/results.json

exit 0
