#!/usr/bin/env bats
# Unit end-to-end tests for verify_projects.sh
#
# These tests invoke the full script (not sourced functions) and verify
# exit codes, output messages, and generated report files.
#
# All tests run in isolated temporary directories.
#
# Validates: Requirements 1.2, 1.3, 1.5, 2.2, 6.2, 7.2

setup() {
    TEST_TEMP_DIR="$(mktemp -d)"
    SCRIPT_DIR="$(cd "$(dirname "${BATS_TEST_FILENAME}")/.." && pwd)"
    SCRIPT_PATH="${SCRIPT_DIR}/verify_projects.sh"
    ORIG_HOME="$HOME"
}

teardown() {
    export HOME="$ORIG_HOME"
    rm -rf "$TEST_TEMP_DIR"
}

# Helper: create a patched script that resolves student home dirs under TEST_TEMP_DIR
create_patched_script() {
    local patched="${TEST_TEMP_DIR}/verify_patched.sh"
    sed "s|home_dir=\"/home/\${student_id}\"|home_dir=\"${TEST_TEMP_DIR}/home/\${student_id}\"|" \
        "$SCRIPT_PATH" > "$patched"
    chmod +x "$patched"
    echo "$patched"
}

# Helper: create a complete valid workspace for a student
create_valid_workspace() {
    local student_id="$1"
    local student_home="${TEST_TEMP_DIR}/home/${student_id}"
    local workspace="${student_home}/eep-software"
    mkdir -p "$workspace"

    # Required directories with README.md in each week folder
    for i in $(seq -w 1 12); do
        mkdir -p "${workspace}/week-${i}"
        echo "# Week ${i}" > "${workspace}/week-${i}/README.md"
    done
    mkdir -p "${workspace}/notes"
    mkdir -p "${workspace}/scripts"
    mkdir -p "${workspace}/capstone"

    # workspace-report.txt
    echo "Workspace report" > "${workspace}/workspace-report.txt"

    # .bashrc with at least 2 aliases
    cat > "${student_home}/.bashrc" << 'BASHRC'
# Shell aliases
alias ll='ls -la'
alias gs='git status'
BASHRC
}

# --- Requirement 1.3: Argument validation ---

@test "zero arguments prints usage message and exits 1" {
    run bash "$SCRIPT_PATH"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Usage: verify_projects.sh <csv_file>"* ]]
}

@test "two arguments prints usage message and exits 1" {
    run bash "$SCRIPT_PATH" "file1.csv" "file2.csv"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Usage: verify_projects.sh <csv_file>"* ]]
}

# --- Requirement 1.2: File not found ---

@test "non-existent CSV file prints error and exits 1" {
    run bash "$SCRIPT_PATH" "${TEST_TEMP_DIR}/does_not_exist.csv"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Error: file not found:"* ]]
    [[ "$output" == *"does_not_exist.csv"* ]]
}

# --- Requirement 1.5: Empty CSV file ---

@test "empty CSV file prints no-IDs error and exits 1" {
    local csv_file="${TEST_TEMP_DIR}/empty.csv"
    touch "$csv_file"
    run bash "$SCRIPT_PATH" "$csv_file"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Error: no student IDs found in"* ]]
}

# --- Requirement 2.2: Missing workspace root ---

@test "missing workspace root causes all checks to FAIL in report" {
    # Student ID with no home directory at all
    local student_id="missing_workspace_student"
    local csv_file="${TEST_TEMP_DIR}/students.csv"
    echo "$student_id" > "$csv_file"

    local patched_script
    patched_script=$(create_patched_script)

    cd "$TEST_TEMP_DIR"
    run bash "$patched_script" "$csv_file"
    [ "$status" -eq 0 ]

    local report_file="${TEST_TEMP_DIR}/${student_id}_EEP1_Week1"
    [ -f "$report_file" ]

    # Every check line (excluding the ID line and Overall line) should be FAIL
    local pass_count
    pass_count=$(grep -c ": PASS" "$report_file" 2>/dev/null || true)
    [ "${pass_count:-0}" -eq 0 ]

    # There should be FAIL entries
    local fail_count
    fail_count=$(grep -c ": FAIL" "$report_file")
    [ "$fail_count" -gt 0 ]

    # Overall must be FAIL
    grep -q "Overall: FAIL" "$report_file"
}

# --- Requirement 7.2 + all checks PASS ---

@test "complete valid workspace produces all PASS checks in report" {
    local student_id="valid_student_001"
    create_valid_workspace "$student_id"

    local csv_file="${TEST_TEMP_DIR}/students.csv"
    echo "$student_id" > "$csv_file"

    local patched_script
    patched_script=$(create_patched_script)

    cd "$TEST_TEMP_DIR"
    run bash "$patched_script" "$csv_file"
    [ "$status" -eq 0 ]

    local report_file="${TEST_TEMP_DIR}/${student_id}_EEP1_Week1"
    [ -f "$report_file" ]

    # First line is the student ID
    local first_line
    first_line=$(head -n 1 "$report_file")
    [ "$first_line" = "$student_id" ]

    # No FAIL entries
    local fail_count
    fail_count=$(grep -c ": FAIL" "$report_file" 2>/dev/null || true)
    [ "${fail_count:-0}" -eq 0 ]

    # Overall is PASS
    grep -q "Overall: PASS" "$report_file"
}

# --- Requirement 7.2: Report overwrite ---

@test "existing report file is overwritten with new results" {
    local student_id="overwrite_student"
    create_valid_workspace "$student_id"

    local csv_file="${TEST_TEMP_DIR}/students.csv"
    echo "$student_id" > "$csv_file"

    local patched_script
    patched_script=$(create_patched_script)

    # Pre-create a report file with stale content
    local report_file="${TEST_TEMP_DIR}/${student_id}_EEP1_Week1"
    echo "STALE OLD CONTENT FROM PREVIOUS RUN" > "$report_file"

    cd "$TEST_TEMP_DIR"
    run bash "$patched_script" "$csv_file"
    [ "$status" -eq 0 ]

    # Report file must exist
    [ -f "$report_file" ]

    # Old content must be gone
    ! grep -q "STALE OLD CONTENT" "$report_file"

    # New content: first line is student ID
    local first_line
    first_line=$(head -n 1 "$report_file")
    [ "$first_line" = "$student_id" ]

    # Must have Overall line from fresh run
    grep -q "Overall: PASS" "$report_file"
}

# --- Requirement 6.2: Grader system folder exclusion ---

@test "grader system folder is never traversed or reported" {
    local student_id="grader_excl_student"
    create_valid_workspace "$student_id"

    # Add a "grader system" folder with content inside the workspace
    local workspace="${TEST_TEMP_DIR}/home/${student_id}/eep-software"
    mkdir -p "${workspace}/grader system/internal"
    echo "secret grader data" > "${workspace}/grader system/scores.txt"

    local csv_file="${TEST_TEMP_DIR}/students.csv"
    echo "$student_id" > "$csv_file"

    local patched_script
    patched_script=$(create_patched_script)

    cd "$TEST_TEMP_DIR"
    run bash "$patched_script" "$csv_file"
    [ "$status" -eq 0 ]

    local report_file="${TEST_TEMP_DIR}/${student_id}_EEP1_Week1"
    [ -f "$report_file" ]

    # "grader system" must not appear anywhere in the report
    ! grep -qi "grader system" "$report_file"
    ! grep -qi "grader.system" "$report_file"

    # The presence of "grader system" folder should not affect other checks
    # All normal checks should still PASS
    local fail_count
    fail_count=$(grep -c ": FAIL" "$report_file" 2>/dev/null || true)
    [ "${fail_count:-0}" -eq 0 ]

    grep -q "Overall: PASS" "$report_file"
}
