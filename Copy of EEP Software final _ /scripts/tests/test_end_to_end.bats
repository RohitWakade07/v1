#!/usr/bin/env bats
# End-to-end integration tests for verify_projects.sh
#
# Tests the script as a whole by invoking it directly with arguments
# and checking exit codes, stderr output, and generated report files.
#
# Validates: Requirements 1.2, 1.3, 1.5, 2.2, 6.2, 7.2

setup() {
    TEST_TEMP_DIR="$(mktemp -d)"
    SCRIPT_DIR="$(cd "$(dirname "${BATS_TEST_FILENAME}")/.." && pwd)"
    SCRIPT_PATH="${SCRIPT_DIR}/verify_projects.sh"
    # Save original HOME
    ORIG_HOME="$HOME"
}

teardown() {
    # Restore HOME
    export HOME="$ORIG_HOME"
    rm -rf "$TEST_TEMP_DIR"
}

# --- Argument validation tests ---

@test "Zero arguments: displays usage message and exits with code 1" {
    run bash "$SCRIPT_PATH"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "Two arguments: displays usage message and exits with code 1" {
    run bash "$SCRIPT_PATH" "arg1" "arg2"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "Non-existent CSV file: displays error and exits with code 1" {
    run bash "$SCRIPT_PATH" "${TEST_TEMP_DIR}/nonexistent_file.csv"
    [ "$status" -eq 1 ]
    [[ "$output" == *"not found"* ]]
}

@test "Empty CSV file: displays error about no student IDs and exits with code 1" {
    local csv_file="${TEST_TEMP_DIR}/empty.csv"
    touch "$csv_file"
    run bash "$SCRIPT_PATH" "$csv_file"
    [ "$status" -eq 1 ]
    [[ "$output" == *"no student IDs"* ]]
}

# --- Workspace verification tests ---

@test "Missing workspace root: all checks FAIL in report" {
    # Use a student ID whose home directory does not exist
    local student_id="nonexistent_test_student_e2e"
    local csv_file="${TEST_TEMP_DIR}/students.csv"
    echo "$student_id" > "$csv_file"

    # Run from temp dir so report is written there
    cd "$TEST_TEMP_DIR"
    run bash "$SCRIPT_PATH" "$csv_file"
    [ "$status" -eq 0 ]

    # Check report file exists
    local report_file="${TEST_TEMP_DIR}/${student_id}_EEP1_Week1"
    [ -f "$report_file" ]

    # All directory checks should be FAIL
    local fail_count
    fail_count=$(grep -c ": FAIL" "$report_file")
    [ "$fail_count" -gt 0 ]

    # No check should be PASS (workspace doesn't exist, so everything fails)
    local pass_count
    pass_count=$(grep -c ": PASS" "$report_file" 2>/dev/null || true)
    [ "${pass_count:-0}" -eq 0 ]

    # Overall should be FAIL
    grep -q "Overall: FAIL" "$report_file"
}

@test "Complete valid workspace: all checks PASS in report" {
    # Create a mock student home directory with a complete workspace
    local student_id="teststu_e2e_valid"
    local student_home="${TEST_TEMP_DIR}/home/${student_id}"
    local workspace="${student_home}/eep-software"
    mkdir -p "$workspace"

    # Create all required directories
    for i in $(seq -w 1 12); do
        mkdir -p "${workspace}/week-${i}"
        echo "# Week ${i}" > "${workspace}/week-${i}/README.md"
    done
    mkdir -p "${workspace}/notes"
    mkdir -p "${workspace}/scripts"
    mkdir -p "${workspace}/capstone"

    # Create workspace-report.txt
    echo "Workspace report content" > "${workspace}/workspace-report.txt"

    # Create .bashrc with 2+ aliases
    cat > "${student_home}/.bashrc" << 'EOF'
# Custom aliases
alias ll='ls -la'
alias gs='git status'
alias gp='git push'
EOF

    # We need the script to look at our mock home directory.
    # The script uses /home/${student_id} as the home dir.
    # We'll create a wrapper that patches the path resolution.
    # Since we can't create /home/teststu_e2e_valid, we create a modified script.
    local patched_script="${TEST_TEMP_DIR}/verify_patched.sh"
    sed "s|home_dir=\"/home/\${student_id}\"|home_dir=\"${TEST_TEMP_DIR}/home/\${student_id}\"|" "$SCRIPT_PATH" > "$patched_script"
    chmod +x "$patched_script"

    # Create CSV
    local csv_file="${TEST_TEMP_DIR}/students.csv"
    echo "$student_id" > "$csv_file"

    # Run from temp dir
    cd "$TEST_TEMP_DIR"
    run bash "$patched_script" "$csv_file"
    [ "$status" -eq 0 ]

    # Check report file exists
    local report_file="${TEST_TEMP_DIR}/${student_id}_EEP1_Week1"
    [ -f "$report_file" ]

    # First line should be the student ID
    local first_line
    first_line=$(head -n 1 "$report_file")
    [ "$first_line" = "$student_id" ]

    # All checks should be PASS
    local fail_count
    fail_count=$(grep -c ": FAIL" "$report_file" 2>/dev/null || true)
    [ "${fail_count:-0}" -eq 0 ]

    # Overall should be PASS
    grep -q "Overall: PASS" "$report_file"
}

@test "Existing report file is overwritten with new results" {
    # Create a mock student with a valid workspace
    local student_id="teststu_e2e_overwrite"
    local student_home="${TEST_TEMP_DIR}/home/${student_id}"
    local workspace="${student_home}/eep-software"
    mkdir -p "$workspace"

    # Create all required directories and READMEs
    for i in $(seq -w 1 12); do
        mkdir -p "${workspace}/week-${i}"
        echo "# Week ${i}" > "${workspace}/week-${i}/README.md"
    done
    mkdir -p "${workspace}/notes"
    mkdir -p "${workspace}/scripts"
    mkdir -p "${workspace}/capstone"
    echo "report" > "${workspace}/workspace-report.txt"
    cat > "${student_home}/.bashrc" << 'EOF'
alias ll='ls -la'
alias gs='git status'
EOF

    # Patch the script to use our temp home
    local patched_script="${TEST_TEMP_DIR}/verify_patched.sh"
    sed "s|home_dir=\"/home/\${student_id}\"|home_dir=\"${TEST_TEMP_DIR}/home/\${student_id}\"|" "$SCRIPT_PATH" > "$patched_script"
    chmod +x "$patched_script"

    local csv_file="${TEST_TEMP_DIR}/students.csv"
    echo "$student_id" > "$csv_file"

    # Create an existing report file with old content
    local report_file="${TEST_TEMP_DIR}/${student_id}_EEP1_Week1"
    echo "OLD CONTENT THAT SHOULD BE OVERWRITTEN" > "$report_file"

    # Run the script
    cd "$TEST_TEMP_DIR"
    run bash "$patched_script" "$csv_file"
    [ "$status" -eq 0 ]

    # Report file should exist and NOT contain old content
    [ -f "$report_file" ]
    ! grep -q "OLD CONTENT THAT SHOULD BE OVERWRITTEN" "$report_file"

    # Report should contain the student ID on first line (new content)
    local first_line
    first_line=$(head -n 1 "$report_file")
    [ "$first_line" = "$student_id" ]

    # Report should have Overall line
    grep -q "Overall:" "$report_file"
}

@test "Grader system folder is never traversed or reported" {
    # Create a workspace that includes a "grader system" folder
    local student_id="teststu_e2e_grader"
    local student_home="${TEST_TEMP_DIR}/home/${student_id}"
    local workspace="${student_home}/eep-software"
    mkdir -p "$workspace"

    # Create all required directories
    for i in $(seq -w 1 12); do
        mkdir -p "${workspace}/week-${i}"
        echo "# Week ${i}" > "${workspace}/week-${i}/README.md"
    done
    mkdir -p "${workspace}/notes"
    mkdir -p "${workspace}/scripts"
    mkdir -p "${workspace}/capstone"
    echo "report" > "${workspace}/workspace-report.txt"
    cat > "${student_home}/.bashrc" << 'EOF'
alias ll='ls -la'
alias gs='git status'
EOF

    # Create the "grader system" folder with some content
    mkdir -p "${workspace}/grader system"
    echo "grader data" > "${workspace}/grader system/data.txt"
    mkdir -p "${workspace}/grader system/subfolder"

    # Patch the script to use our temp home
    local patched_script="${TEST_TEMP_DIR}/verify_patched.sh"
    sed "s|home_dir=\"/home/\${student_id}\"|home_dir=\"${TEST_TEMP_DIR}/home/\${student_id}\"|" "$SCRIPT_PATH" > "$patched_script"
    chmod +x "$patched_script"

    local csv_file="${TEST_TEMP_DIR}/students.csv"
    echo "$student_id" > "$csv_file"

    # Run the script
    cd "$TEST_TEMP_DIR"
    run bash "$patched_script" "$csv_file"
    [ "$status" -eq 0 ]

    # Check report file exists
    local report_file="${TEST_TEMP_DIR}/${student_id}_EEP1_Week1"
    [ -f "$report_file" ]

    # "grader system" should NOT appear anywhere in the report
    ! grep -qi "grader system" "$report_file"
    ! grep -qi "grader.system" "$report_file"

    # The report should still have all the normal checks
    grep -q "Overall:" "$report_file"

    # All checks should PASS (the grader system folder should not cause any issues)
    local fail_count
    fail_count=$(grep -c ": FAIL" "$report_file" 2>/dev/null || true)
    [ "${fail_count:-0}" -eq 0 ]
    grep -q "Overall: PASS" "$report_file"
}
