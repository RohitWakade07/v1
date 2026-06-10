#!/usr/bin/env bats
# Feature: student-project-verifier, Property 2: Directory verification accuracy
#
# Property 2: For any workspace state (random subset of required directories
# present as directories, present as files, or absent), the directory check
# results shall report PASS for each required directory that exists as an actual
# directory, and FAIL for each required directory that is missing or exists as a
# non-directory file.
#
# Validates: Requirements 2.3, 2.4, 2.5, 2.6, 2.7

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

# Helper: create a random workspace state
# For each required directory, randomly choose one of:
#   0 = absent (don't create it)
#   1 = create as a real directory
#   2 = create as a regular file (not a directory)
# Sets EXPECTED_RESULTS associative array with dir_name -> PASS/FAIL
create_random_workspace() {
    local workspace="$1"
    mkdir -p "$workspace"

    # REQUIRED_DIRS from the script
    local dirs=(week-01 week-02 week-03 week-04 week-05 week-06 week-07 week-08 week-09 week-10 week-11 week-12 notes scripts capstone)

    EXPECTED_PASS_DIRS=()
    EXPECTED_FAIL_DIRS=()

    for dir in "${dirs[@]}"; do
        local choice=$((RANDOM % 3))
        case $choice in
            0)
                # Absent - do nothing
                EXPECTED_FAIL_DIRS+=("$dir")
                ;;
            1)
                # Create as a real directory
                mkdir -p "${workspace}/${dir}"
                EXPECTED_PASS_DIRS+=("$dir")
                ;;
            2)
                # Create as a regular file (not a directory)
                touch "${workspace}/${dir}"
                EXPECTED_FAIL_DIRS+=("$dir")
                ;;
        esac
    done
}

@test "Property 2: Directory verification accuracy across ${NUM_ITERATIONS} random workspace states" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        # Create a fresh workspace for this iteration
        local workspace="${TEST_TEMP_DIR}/iter_${iteration}/eep-software"
        mkdir -p "${TEST_TEMP_DIR}/iter_${iteration}"

        # Create random workspace state
        create_random_workspace "$workspace"

        # Source functions and reset CHECK_RESULTS
        source_functions
        CHECK_RESULTS=()

        # Run verify_directories
        verify_directories "$workspace"

        # Verify results for directories expected to PASS
        for dir in "${EXPECTED_PASS_DIRS[@]}"; do
            local found=false
            for result in "${CHECK_RESULTS[@]}"; do
                if [[ "$result" == "dir:${dir}: PASS" ]]; then
                    found=true
                    break
                fi
            done
            if [[ "$found" != true ]]; then
                echo "FAILED at iteration $iteration"
                echo "Expected 'dir:${dir}: PASS' but not found in results"
                echo "Workspace contents:"
                ls -la "$workspace" 2>/dev/null || echo "(workspace missing)"
                echo "CHECK_RESULTS: ${CHECK_RESULTS[*]}"
                return 1
            fi
        done

        # Verify results for directories expected to FAIL
        for dir in "${EXPECTED_FAIL_DIRS[@]}"; do
            local found=false
            for result in "${CHECK_RESULTS[@]}"; do
                if [[ "$result" == "dir:${dir}: FAIL" ]]; then
                    found=true
                    break
                fi
            done
            if [[ "$found" != true ]]; then
                echo "FAILED at iteration $iteration"
                echo "Expected 'dir:${dir}: FAIL' but not found in results"
                echo "Workspace contents:"
                ls -la "$workspace" 2>/dev/null || echo "(workspace missing)"
                echo "CHECK_RESULTS: ${CHECK_RESULTS[*]}"
                return 1
            fi
        done

        # Verify total number of results matches number of required dirs
        if [[ ${#CHECK_RESULTS[@]} -ne 15 ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected 15 results (one per required dir), got ${#CHECK_RESULTS[@]}"
            echo "CHECK_RESULTS: ${CHECK_RESULTS[*]}"
            return 1
        fi
    done
}

@test "Property 2: Missing workspace root marks all directories as FAIL" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        # Use a non-existent workspace path
        local workspace="${TEST_TEMP_DIR}/nonexistent_${iteration}/eep-software"

        # Source functions and reset CHECK_RESULTS
        source_functions
        CHECK_RESULTS=()

        # Run verify_directories on non-existent workspace
        verify_directories "$workspace"

        # All 15 required directories should be FAIL
        if [[ ${#CHECK_RESULTS[@]} -ne 15 ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected 15 FAIL results for missing workspace, got ${#CHECK_RESULTS[@]}"
            echo "CHECK_RESULTS: ${CHECK_RESULTS[*]}"
            return 1
        fi

        # Verify each result is FAIL
        for result in "${CHECK_RESULTS[@]}"; do
            if [[ "$result" != *": FAIL" ]]; then
                echo "FAILED at iteration $iteration"
                echo "Expected all FAIL for missing workspace, got: $result"
                return 1
            fi
        done
    done
}

@test "Property 2: All directories present as real directories yields all PASS" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local workspace="${TEST_TEMP_DIR}/allpass_${iteration}/eep-software"
        mkdir -p "$workspace"

        # Create all required directories
        local dirs=(week-01 week-02 week-03 week-04 week-05 week-06 week-07 week-08 week-09 week-10 week-11 week-12 notes scripts capstone)
        for dir in "${dirs[@]}"; do
            mkdir -p "${workspace}/${dir}"
        done

        # Source functions and reset CHECK_RESULTS
        source_functions
        CHECK_RESULTS=()

        # Run verify_directories
        verify_directories "$workspace"

        # All 15 should be PASS
        if [[ ${#CHECK_RESULTS[@]} -ne 15 ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected 15 results, got ${#CHECK_RESULTS[@]}"
            return 1
        fi

        for result in "${CHECK_RESULTS[@]}"; do
            if [[ "$result" != *": PASS" ]]; then
                echo "FAILED at iteration $iteration"
                echo "Expected all PASS, got: $result"
                return 1
            fi
        done
    done
}
