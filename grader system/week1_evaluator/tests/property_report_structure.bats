#!/usr/bin/env bats
# Feature: student-project-verifier, Property 6: Report structure correctness
#
# Property 6: For any student ID and any set of verification results, the generated
# report file shall be named exactly [ID]_EEP1_Week1, contain the student ID on the
# first line, list exactly one line per verification check in the format
# "<check_name>: PASS|FAIL", and end with a summary line.
#
# Validates: Requirements 7.1, 7.3, 7.4, 7.5

# Number of random iterations to run
NUM_ITERATIONS=20

setup() {
    TEST_TEMP_DIR="$(mktemp -d)"
    SCRIPT_DIR="$(cd "$(dirname "${BATS_TEST_FILENAME}")/.." && pwd)"
    SCRIPT_PATH="${SCRIPT_DIR}/verify_projects.sh"
}

teardown() {
    rm -rf "$TEST_TEMP_DIR"
}

# Helper: source only the function definitions from the script, not the main body
source_functions() {
    eval "$(sed -n '1,/^# --- Main ---/p' "$SCRIPT_PATH" | head -n -1)"
}

# Helper: generate a random alphanumeric student ID of random length (3-15 chars)
random_student_id() {
    local length=$(( (RANDOM % 13) + 3 ))
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c "$length"
}

# Helper: generate a random check name (simulating real check names)
random_check_name() {
    local check_types=("dir:week-01" "dir:week-02" "dir:week-03" "dir:week-04"
                       "dir:week-05" "dir:week-06" "dir:week-07" "dir:week-08"
                       "dir:week-09" "dir:week-10" "dir:week-11" "dir:week-12"
                       "dir:notes" "dir:scripts" "dir:capstone"
                       "readme:week-01" "readme:week-02" "readme:week-03"
                       "readme:week-04" "readme:week-05" "readme:week-06"
                       "readme:week-07" "readme:week-08" "readme:week-09"
                       "readme:week-10" "readme:week-11" "readme:week-12"
                       "bashrc" "workspace-report")
    local idx=$(( RANDOM % ${#check_types[@]} ))
    echo "${check_types[$idx]}"
}

# Helper: generate a random CHECK_RESULTS array with 1-30 entries
generate_random_results() {
    CHECK_RESULTS=()
    local num_checks=$(( (RANDOM % 30) + 1 ))
    for ((i = 0; i < num_checks; i++)); do
        local check_name
        check_name=$(random_check_name)
        local status
        if ((RANDOM % 2 == 0)); then
            status="PASS"
        else
            status="FAIL"
        fi
        CHECK_RESULTS+=("${check_name}: ${status}")
    done
}

@test "Property 6: Report file is named exactly [ID]_EEP1_Week1 - ${NUM_ITERATIONS} iterations" {
    # **Validates: Requirements 7.1**
    source_functions

    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local student_id
        student_id=$(random_student_id)

        generate_random_results

        local report_dir="${TEST_TEMP_DIR}/naming_${iteration}"
        mkdir -p "$report_dir"
        cd "$report_dir"

        generate_report "$student_id"

        local expected_file="${report_dir}/${student_id}_EEP1_Week1"
        if [[ ! -f "$expected_file" ]]; then
            echo "FAILED at iteration $iteration"
            echo "Student ID: '$student_id'"
            echo "Expected file: '$expected_file'"
            echo "Files in directory:"
            ls -la "$report_dir"
            return 1
        fi

        cd "$TEST_TEMP_DIR"
    done
}

@test "Property 6: First line of report is the student ID - ${NUM_ITERATIONS} iterations" {
    # **Validates: Requirements 7.3**
    source_functions

    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local student_id
        student_id=$(random_student_id)

        generate_random_results

        local report_dir="${TEST_TEMP_DIR}/firstline_${iteration}"
        mkdir -p "$report_dir"
        cd "$report_dir"

        generate_report "$student_id"

        local report_file="${report_dir}/${student_id}_EEP1_Week1"
        local first_line
        first_line=$(head -1 "$report_file")

        if [[ "$first_line" != "$student_id" ]]; then
            echo "FAILED at iteration $iteration"
            echo "Student ID: '$student_id'"
            echo "First line of report: '$first_line'"
            echo "Full report:"
            cat "$report_file"
            return 1
        fi

        cd "$TEST_TEMP_DIR"
    done
}

@test "Property 6: Each check result is one line in format 'check_name: PASS|FAIL' - ${NUM_ITERATIONS} iterations" {
    # **Validates: Requirements 7.4**
    source_functions

    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local student_id
        student_id=$(random_student_id)

        generate_random_results
        local num_checks=${#CHECK_RESULTS[@]}

        local report_dir="${TEST_TEMP_DIR}/format_${iteration}"
        mkdir -p "$report_dir"
        cd "$report_dir"

        generate_report "$student_id"

        local report_file="${report_dir}/${student_id}_EEP1_Week1"

        # Read middle lines (skip first line = ID, skip last line = Overall)
        local total_lines
        total_lines=$(wc -l < "$report_file")

        # Expected total lines: 1 (ID) + num_checks (results) + 1 (Overall)
        local expected_lines=$(( num_checks + 2 ))
        if [[ "$total_lines" -ne "$expected_lines" ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected $expected_lines lines (1 ID + $num_checks checks + 1 Overall), got $total_lines"
            echo "CHECK_RESULTS had $num_checks entries"
            echo "Full report:"
            cat "$report_file"
            return 1
        fi

        # Verify each middle line matches the format "something: PASS" or "something: FAIL"
        local line_num=0
        while IFS= read -r line; do
            line_num=$((line_num + 1))
            # Skip first line (student ID) and last line (Overall)
            if [[ $line_num -eq 1 ]] || [[ $line_num -eq $total_lines ]]; then
                continue
            fi

            # Each check line must end with ": PASS" or ": FAIL"
            if [[ "$line" != *": PASS" ]] && [[ "$line" != *": FAIL" ]]; then
                echo "FAILED at iteration $iteration, line $line_num"
                echo "Line does not match format 'check_name: PASS|FAIL': '$line'"
                echo "Full report:"
                cat "$report_file"
                return 1
            fi
        done < "$report_file"

        cd "$TEST_TEMP_DIR"
    done
}

@test "Property 6: Last line is summary 'Overall: PASS' or 'Overall: FAIL' - ${NUM_ITERATIONS} iterations" {
    # **Validates: Requirements 7.5**
    source_functions

    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local student_id
        student_id=$(random_student_id)

        generate_random_results

        local report_dir="${TEST_TEMP_DIR}/summary_${iteration}"
        mkdir -p "$report_dir"
        cd "$report_dir"

        generate_report "$student_id"

        local report_file="${report_dir}/${student_id}_EEP1_Week1"
        local last_line
        last_line=$(tail -1 "$report_file")

        if [[ "$last_line" != "Overall: PASS" ]] && [[ "$last_line" != "Overall: FAIL" ]]; then
            echo "FAILED at iteration $iteration"
            echo "Student ID: '$student_id'"
            echo "Last line: '$last_line'"
            echo "Expected: 'Overall: PASS' or 'Overall: FAIL'"
            echo "Full report:"
            cat "$report_file"
            return 1
        fi

        cd "$TEST_TEMP_DIR"
    done
}
