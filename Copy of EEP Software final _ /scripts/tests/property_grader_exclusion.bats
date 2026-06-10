#!/usr/bin/env bats
# Feature: student-project-verifier, Property 5: Grader system folder exclusion
#
# Property 5: For any workspace state (with or without a "grader system" folder
# present), the generated Student_Report shall never contain any line referencing
# the "grader system" folder — it shall not appear as a PASS, FAIL, or any other
# check entry.
#
# Validates: Requirements 6.1, 6.3

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

# Helper: generate a random alphanumeric string of given length
random_id() {
    local length="${1:-8}"
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c "$length"
}

# Helper: create a random workspace with a random subset of required directories
# and optionally include the "grader system" folder
create_random_workspace() {
    local workspace="$1"
    local include_grader="$2"  # "yes" or "no"

    mkdir -p "$workspace"

    # Randomly create some of the required directories
    local all_dirs=(week-01 week-02 week-03 week-04 week-05 week-06 week-07 week-08 week-09 week-10 week-11 week-12 notes scripts capstone)
    for dir in "${all_dirs[@]}"; do
        if ((RANDOM % 2 == 0)); then
            mkdir -p "${workspace}/${dir}"
            # Randomly add README.md to week directories
            if [[ "$dir" == week-* ]] && ((RANDOM % 2 == 0)); then
                echo "# Week" > "${workspace}/${dir}/README.md"
            fi
        fi
    done

    # Conditionally create the "grader system" folder
    if [[ "$include_grader" == "yes" ]]; then
        mkdir -p "${workspace}/grader system"
        # Optionally add some content inside it
        if ((RANDOM % 2 == 0)); then
            echo "grader content" > "${workspace}/grader system/config.txt"
        fi
    fi
}

@test "Property 5: Grader system folder never appears in CHECK_RESULTS - ${NUM_ITERATIONS} iterations" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        # Randomly decide whether to include "grader system"
        local include_grader
        if ((RANDOM % 2 == 0)); then
            include_grader="yes"
        else
            include_grader="no"
        fi

        local workspace="${TEST_TEMP_DIR}/iter_${iteration}"
        create_random_workspace "$workspace" "$include_grader"

        # Source functions and run verify_directories
        source_functions
        CHECK_RESULTS=()
        verify_directories "$workspace"

        # Verify: no entry in CHECK_RESULTS contains "grader system"
        for entry in "${CHECK_RESULTS[@]}"; do
            if [[ "$entry" == *"grader system"* ]]; then
                echo "FAILED at iteration $iteration (grader present: $include_grader)"
                echo "Found 'grader system' in CHECK_RESULTS entry: '$entry'"
                echo "Workspace contents:"
                ls -la "$workspace"
                echo "All CHECK_RESULTS:"
                printf '  %s\n' "${CHECK_RESULTS[@]}"
                return 1
            fi
        done
    done
}

@test "Property 5: Grader system folder never appears in generated report output - ${NUM_ITERATIONS} iterations" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        # Randomly decide whether to include "grader system"
        local include_grader
        if ((RANDOM % 2 == 0)); then
            include_grader="yes"
        else
            include_grader="no"
        fi

        local workspace="${TEST_TEMP_DIR}/report_${iteration}"
        create_random_workspace "$workspace" "$include_grader"

        # Source functions and run all verification steps
        source_functions
        CHECK_RESULTS=()
        verify_directories "$workspace"

        # Generate a report using a random student ID
        local student_id
        student_id="student$(random_id 5)"
        local report_dir="${TEST_TEMP_DIR}/reports_${iteration}"
        mkdir -p "$report_dir"

        # Generate report in the report directory
        cd "$report_dir"
        generate_report "$student_id"
        cd "$TEST_TEMP_DIR"

        local report_file="${report_dir}/${student_id}_EEP1_Week1"

        # Verify: no line in the report file contains "grader system"
        if [[ -f "$report_file" ]]; then
            if grep -q "grader system" "$report_file"; then
                echo "FAILED at iteration $iteration (grader present: $include_grader)"
                echo "Found 'grader system' in report file:"
                grep "grader system" "$report_file"
                echo "Full report contents:"
                cat "$report_file"
                return 1
            fi
        else
            echo "FAILED at iteration $iteration: report file not generated at $report_file"
            return 1
        fi
    done
}

@test "Property 5: Grader system with explicit presence always excluded - ${NUM_ITERATIONS} iterations" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        # Always include "grader system" folder to stress-test exclusion
        local workspace="${TEST_TEMP_DIR}/always_${iteration}"
        create_random_workspace "$workspace" "yes"

        # Source functions and run verify_directories
        source_functions
        CHECK_RESULTS=()
        verify_directories "$workspace"

        # Verify: no entry in CHECK_RESULTS contains "grader system"
        for entry in "${CHECK_RESULTS[@]}"; do
            if [[ "$entry" == *"grader system"* ]]; then
                echo "FAILED at iteration $iteration"
                echo "Found 'grader system' in CHECK_RESULTS entry: '$entry'"
                echo "Workspace contents:"
                ls -la "$workspace"
                echo "All CHECK_RESULTS:"
                printf '  %s\n' "${CHECK_RESULTS[@]}"
                return 1
            fi
        done

        # Also verify via report generation
        local student_id
        student_id="stu$(random_id 4)"
        local report_dir="${TEST_TEMP_DIR}/alwaysrpt_${iteration}"
        mkdir -p "$report_dir"

        cd "$report_dir"
        generate_report "$student_id"
        cd "$TEST_TEMP_DIR"

        local report_file="${report_dir}/${student_id}_EEP1_Week1"
        if [[ -f "$report_file" ]] && grep -q "grader system" "$report_file"; then
            echo "FAILED at iteration $iteration"
            echo "Found 'grader system' in report output:"
            cat "$report_file"
            return 1
        fi
    done
}
