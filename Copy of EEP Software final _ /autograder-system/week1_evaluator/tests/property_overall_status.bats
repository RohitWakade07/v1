#!/usr/bin/env bats
# Feature: student-project-verifier, Property 7: Overall status logic
#
# Property 7: For any set of individual check results, the overall summary
# status shall be PASS if and only if every individual check is PASS; if any
# single check is FAIL, the overall status shall be FAIL.
#
# Validates: Requirements 7.6, 7.7

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

# Helper: generate a random check name
random_check_name() {
    local prefixes=("dir:week-" "dir:" "readme:week-" "bashrc" "workspace-report" "custom-check-")
    local idx=$((RANDOM % ${#prefixes[@]}))
    local prefix="${prefixes[$idx]}"
    if [[ "$prefix" == "bashrc" || "$prefix" == "workspace-report" ]]; then
        echo "$prefix"
    else
        echo "${prefix}$(printf '%02d' $((RANDOM % 12 + 1)))"
    fi
}

@test "Property 7: Overall = PASS iff all checks = PASS - ${NUM_ITERATIONS} iterations" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        source_functions

        # Generate a random number of check results (between 1 and 20)
        local num_checks=$(( (RANDOM % 20) + 1 ))

        # Randomly decide if this iteration should be all-PASS or have at least one FAIL
        local force_all_pass=$((RANDOM % 2))

        CHECK_RESULTS=()
        local expected_overall="PASS"

        for ((c = 1; c <= num_checks; c++)); do
            local check_name
            check_name="$(random_check_name)"

            if [[ "$force_all_pass" -eq 1 ]]; then
                # All checks pass
                CHECK_RESULTS+=("${check_name}: PASS")
            else
                # Randomly assign PASS or FAIL
                if ((RANDOM % 3 == 0)); then
                    CHECK_RESULTS+=("${check_name}: FAIL")
                    expected_overall="FAIL"
                else
                    CHECK_RESULTS+=("${check_name}: PASS")
                fi
            fi
        done

        # If we randomly assigned and nothing ended up FAIL, expected is still PASS
        # (This is correct — if all random assignments happened to be PASS, overall is PASS)

        # Generate report
        local student_id="stu$(random_id 5)"
        local report_dir="${TEST_TEMP_DIR}/iter_${iteration}"
        mkdir -p "$report_dir"

        cd "$report_dir"
        generate_report "$student_id"
        cd "$TEST_TEMP_DIR"

        local report_file="${report_dir}/${student_id}_EEP1_Week1"

        # Verify report was generated
        if [[ ! -f "$report_file" ]]; then
            echo "FAILED at iteration $iteration: report file not generated"
            return 1
        fi

        # Extract the Overall line from the report
        local overall_line
        overall_line="$(grep '^Overall:' "$report_file")"

        if [[ -z "$overall_line" ]]; then
            echo "FAILED at iteration $iteration: no Overall line found in report"
            echo "Report contents:"
            cat "$report_file"
            return 1
        fi

        # Extract the status from the Overall line
        local actual_overall
        actual_overall="$(echo "$overall_line" | sed 's/^Overall: //')"

        if [[ "$actual_overall" != "$expected_overall" ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected overall: $expected_overall"
            echo "Actual overall: $actual_overall"
            echo "CHECK_RESULTS:"
            printf '  %s\n' "${CHECK_RESULTS[@]}"
            echo "Report contents:"
            cat "$report_file"
            return 1
        fi
    done
}

@test "Property 7: All PASS results always produce overall PASS - ${NUM_ITERATIONS} iterations" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        source_functions

        # Generate a random number of check results (between 1 and 25), all PASS
        local num_checks=$(( (RANDOM % 25) + 1 ))

        CHECK_RESULTS=()
        for ((c = 1; c <= num_checks; c++)); do
            local check_name
            check_name="$(random_check_name)"
            CHECK_RESULTS+=("${check_name}: PASS")
        done

        # Generate report
        local student_id="pass$(random_id 4)"
        local report_dir="${TEST_TEMP_DIR}/allpass_${iteration}"
        mkdir -p "$report_dir"

        cd "$report_dir"
        generate_report "$student_id"
        cd "$TEST_TEMP_DIR"

        local report_file="${report_dir}/${student_id}_EEP1_Week1"

        if [[ ! -f "$report_file" ]]; then
            echo "FAILED at iteration $iteration: report file not generated"
            return 1
        fi

        local overall_line
        overall_line="$(grep '^Overall:' "$report_file")"
        local actual_overall
        actual_overall="$(echo "$overall_line" | sed 's/^Overall: //')"

        if [[ "$actual_overall" != "PASS" ]]; then
            echo "FAILED at iteration $iteration: expected PASS but got $actual_overall"
            echo "CHECK_RESULTS (all should be PASS):"
            printf '  %s\n' "${CHECK_RESULTS[@]}"
            echo "Report contents:"
            cat "$report_file"
            return 1
        fi
    done
}

@test "Property 7: Any single FAIL produces overall FAIL - ${NUM_ITERATIONS} iterations" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        source_functions

        # Generate a random number of check results (between 2 and 20)
        local num_checks=$(( (RANDOM % 19) + 2 ))

        # Pick a random position to place the single FAIL
        local fail_pos=$(( RANDOM % num_checks ))

        CHECK_RESULTS=()
        for ((c = 0; c < num_checks; c++)); do
            local check_name
            check_name="$(random_check_name)"
            if [[ "$c" -eq "$fail_pos" ]]; then
                CHECK_RESULTS+=("${check_name}: FAIL")
            else
                CHECK_RESULTS+=("${check_name}: PASS")
            fi
        done

        # Generate report
        local student_id="fail$(random_id 4)"
        local report_dir="${TEST_TEMP_DIR}/onefail_${iteration}"
        mkdir -p "$report_dir"

        cd "$report_dir"
        generate_report "$student_id"
        cd "$TEST_TEMP_DIR"

        local report_file="${report_dir}/${student_id}_EEP1_Week1"

        if [[ ! -f "$report_file" ]]; then
            echo "FAILED at iteration $iteration: report file not generated"
            return 1
        fi

        local overall_line
        overall_line="$(grep '^Overall:' "$report_file")"
        local actual_overall
        actual_overall="$(echo "$overall_line" | sed 's/^Overall: //')"

        if [[ "$actual_overall" != "FAIL" ]]; then
            echo "FAILED at iteration $iteration: expected FAIL but got $actual_overall"
            echo "FAIL was at position $fail_pos of $num_checks checks"
            echo "CHECK_RESULTS:"
            printf '  %s\n' "${CHECK_RESULTS[@]}"
            echo "Report contents:"
            cat "$report_file"
            return 1
        fi
    done
}
