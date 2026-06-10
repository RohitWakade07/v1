#!/usr/bin/env bash

# Simulate the function (copied from verify_projects.sh for isolated testing)
generate_report() {
    local student_id="$1"
    local report_file="${student_id}_EEP1_Week1"

    # Determine overall status: PASS only if all checks pass
    local overall="PASS"
    for result in "${CHECK_RESULTS[@]}"; do
        if [[ "$result" == *": FAIL" ]]; then
            overall="FAIL"
            break
        fi
    done

    # Write report file (overwrites existing)
    {
        echo "$student_id"
        for result in "${CHECK_RESULTS[@]}"; do
            echo "$result"
        done
        echo "Overall: $overall"
    } > "$report_file"
}

PASS_COUNT=0
FAIL_COUNT=0

assert_eq() {
    local desc="$1" expected="$2" actual="$3"
    if [[ "$expected" == "$actual" ]]; then
        echo "  PASS: $desc"
        ((PASS_COUNT++))
    else
        echo "  FAIL: $desc (expected '$expected', got '$actual')"
        ((FAIL_COUNT++))
    fi
}

# Test 1: All checks pass
echo "=== Test 1: All checks PASS ==="
CHECK_RESULTS=("dir:week-01: PASS" "dir:week-02: PASS" "readme:week-01: PASS" "bashrc: PASS" "workspace-report: PASS")
generate_report "student001"

assert_eq "File created with correct name" "yes" "$( [[ -f student001_EEP1_Week1 ]] && echo yes || echo no )"
assert_eq "First line is student ID" "student001" "$(head -1 student001_EEP1_Week1)"
assert_eq "Last line is Overall: PASS" "Overall: PASS" "$(tail -1 student001_EEP1_Week1)"
assert_eq "Line count is 7 (ID + 5 checks + Overall)" "7" "$(wc -l < student001_EEP1_Week1)"

echo ""

# Test 2: One check fails → Overall: FAIL
echo "=== Test 2: One check FAIL ==="
CHECK_RESULTS=("dir:week-01: PASS" "dir:week-02: FAIL" "readme:week-01: PASS" "bashrc: PASS" "workspace-report: PASS")
generate_report "student002"

assert_eq "Last line is Overall: FAIL" "Overall: FAIL" "$(tail -1 student002_EEP1_Week1)"
assert_eq "Second line is first check" "dir:week-01: PASS" "$(sed -n '2p' student002_EEP1_Week1)"
assert_eq "Third line is second check" "dir:week-02: FAIL" "$(sed -n '3p' student002_EEP1_Week1)"

echo ""

# Test 3: Overwrite existing file
echo "=== Test 3: Overwrite existing file ==="
echo "old content" > student003_EEP1_Week1
CHECK_RESULTS=("bashrc: PASS" "workspace-report: PASS")
generate_report "student003"

assert_eq "File was overwritten (first line is student ID)" "student003" "$(head -1 student003_EEP1_Week1)"
assert_eq "Old content is gone (ID + 2 checks + Overall = 4)" "4" "$(wc -l < student003_EEP1_Week1)"

echo ""

# Test 4: All checks fail
echo "=== Test 4: All checks FAIL ==="
CHECK_RESULTS=("dir:week-01: FAIL" "readme:week-01: FAIL" "bashrc: FAIL" "workspace-report: FAIL")
generate_report "student004"

assert_eq "Last line is Overall: FAIL" "Overall: FAIL" "$(tail -1 student004_EEP1_Week1)"
assert_eq "Line count is 6 (ID + 4 checks + Overall)" "6" "$(wc -l < student004_EEP1_Week1)"

echo ""

# Test 5: Empty CHECK_RESULTS → Overall: PASS (vacuously true)
echo "=== Test 5: Empty CHECK_RESULTS ==="
CHECK_RESULTS=()
generate_report "student005"

assert_eq "First line is student ID" "student005" "$(head -1 student005_EEP1_Week1)"
assert_eq "Last line is Overall: PASS" "Overall: PASS" "$(tail -1 student005_EEP1_Week1)"
assert_eq "Line count is 2 (ID + Overall)" "2" "$(wc -l < student005_EEP1_Week1)"

echo ""

# Summary
echo "=== Summary ==="
echo "Passed: $PASS_COUNT, Failed: $FAIL_COUNT"

# Cleanup
rm -f student001_EEP1_Week1 student002_EEP1_Week1 student003_EEP1_Week1 student004_EEP1_Week1 student005_EEP1_Week1

if [[ $FAIL_COUNT -gt 0 ]]; then
    exit 1
fi
