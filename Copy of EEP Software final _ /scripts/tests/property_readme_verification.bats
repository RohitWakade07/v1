#!/usr/bin/env bats
# Feature: student-project-verifier, Property 3: README verification accuracy
#
# Property 3: For any workspace state with week-01 through week-12 directories
# containing or lacking README.md files (as regular files, directories, or
# wrong-case variants), the README check results shall report PASS only when a
# case-sensitive regular file named exactly `README.md` exists in the
# corresponding week folder, and FAIL otherwise.
#
# Validates: Requirements 3.1, 3.2, 3.3

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

# Helper: create a workspace with week-01 through week-12 directories
# and randomly place/remove README.md in each
# Sets EXPECTED_RESULTS associative array with expected PASS/FAIL per week
create_random_workspace() {
    local workspace="$1"
    mkdir -p "$workspace"

    # Create all week directories
    for week_num in $(seq -w 1 12); do
        local week_dir="${workspace}/week-${week_num}"
        mkdir -p "$week_dir"
    done

    # For each week, randomly decide what to do with README.md
    EXPECTED_RESULTS=()
    for week_num in $(seq -w 1 12); do
        local week_dir="${workspace}/week-${week_num}"
        local choice=$((RANDOM % 5))

        case $choice in
            0)
                # Place README.md as a regular file (should PASS)
                echo "# Week ${week_num}" > "${week_dir}/README.md"
                EXPECTED_RESULTS+=("PASS")
                ;;
            1)
                # Place README.md as a directory (should FAIL)
                mkdir -p "${week_dir}/README.md"
                EXPECTED_RESULTS+=("FAIL")
                ;;
            2)
                # Use wrong case: readme.md (should FAIL)
                echo "# Week ${week_num}" > "${week_dir}/readme.md"
                EXPECTED_RESULTS+=("FAIL")
                ;;
            3)
                # Use wrong case: Readme.md (should FAIL)
                echo "# Week ${week_num}" > "${week_dir}/Readme.md"
                EXPECTED_RESULTS+=("FAIL")
                ;;
            4)
                # Omit README.md entirely (should FAIL)
                EXPECTED_RESULTS+=("FAIL")
                ;;
        esac
    done
}

@test "Property 3: README verification accuracy across ${NUM_ITERATIONS} random workspace states" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        # Create a fresh workspace for this iteration
        local workspace="${TEST_TEMP_DIR}/iter_${iteration}/eep-software"
        rm -rf "${TEST_TEMP_DIR}/iter_${iteration}"
        mkdir -p "${TEST_TEMP_DIR}/iter_${iteration}"

        # Generate random workspace state
        create_random_workspace "$workspace"

        # Source functions and run verify_readmes
        source_functions
        CHECK_RESULTS=()
        verify_readmes "$workspace"

        # Verify we got exactly 12 results
        if [[ ${#CHECK_RESULTS[@]} -ne 12 ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected 12 results, got ${#CHECK_RESULTS[@]}"
            echo "Results: ${CHECK_RESULTS[*]}"
            return 1
        fi

        # Verify each result matches expected
        for ((i = 0; i < 12; i++)); do
            local week_num
            printf -v week_num "%02d" $((i + 1))
            local expected="${EXPECTED_RESULTS[$i]}"
            local actual="${CHECK_RESULTS[$i]}"
            local expected_line="readme:week-${week_num}: ${expected}"

            if [[ "$actual" != "$expected_line" ]]; then
                echo "FAILED at iteration $iteration, week-${week_num}"
                echo "Expected: '${expected_line}'"
                echo "Actual:   '${actual}'"
                echo "Workspace contents of week-${week_num}:"
                ls -la "${workspace}/week-${week_num}/"
                return 1
            fi
        done
    done
}

@test "Property 3: README verification reports FAIL when week directory has only wrong-case variants" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local workspace="${TEST_TEMP_DIR}/case_${iteration}/eep-software"
        rm -rf "${TEST_TEMP_DIR}/case_${iteration}"
        mkdir -p "$workspace"

        # Create all week directories with only wrong-case README variants
        local wrong_cases=("readme.md" "Readme.md" "README.MD" "ReadMe.md" "readme.MD" "README.Md")
        EXPECTED_RESULTS=()

        for week_num in $(seq -w 1 12); do
            local week_dir="${workspace}/week-${week_num}"
            mkdir -p "$week_dir"

            # Pick a random wrong-case variant
            local variant_idx=$((RANDOM % ${#wrong_cases[@]}))
            local variant="${wrong_cases[$variant_idx]}"
            echo "# Content" > "${week_dir}/${variant}"
            EXPECTED_RESULTS+=("FAIL")
        done

        # Source functions and run verify_readmes
        source_functions
        CHECK_RESULTS=()
        verify_readmes "$workspace"

        # All should be FAIL since none have exact "README.md"
        for ((i = 0; i < 12; i++)); do
            local week_num
            printf -v week_num "%02d" $((i + 1))
            local actual="${CHECK_RESULTS[$i]}"
            local expected_line="readme:week-${week_num}: FAIL"

            if [[ "$actual" != "$expected_line" ]]; then
                echo "FAILED at iteration $iteration, week-${week_num}"
                echo "Expected: '${expected_line}'"
                echo "Actual:   '${actual}'"
                echo "Workspace contents:"
                ls -la "${workspace}/week-${week_num}/"
                return 1
            fi
        done
    done
}

@test "Property 3: README verification reports PASS only for regular files named exactly README.md" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local workspace="${TEST_TEMP_DIR}/exact_${iteration}/eep-software"
        rm -rf "${TEST_TEMP_DIR}/exact_${iteration}"
        mkdir -p "$workspace"

        EXPECTED_RESULTS=()

        for week_num in $(seq -w 1 12); do
            local week_dir="${workspace}/week-${week_num}"
            mkdir -p "$week_dir"

            # Randomly decide: correct README.md file, or README.md as directory
            local choice=$((RANDOM % 2))
            case $choice in
                0)
                    # Regular file named exactly README.md -> PASS
                    echo "# Week ${week_num} content $(cat /dev/urandom | tr -dc 'a-z' | head -c 10)" > "${week_dir}/README.md"
                    EXPECTED_RESULTS+=("PASS")
                    ;;
                1)
                    # README.md as a directory -> FAIL
                    mkdir -p "${week_dir}/README.md"
                    EXPECTED_RESULTS+=("FAIL")
                    ;;
            esac
        done

        # Source functions and run verify_readmes
        source_functions
        CHECK_RESULTS=()
        verify_readmes "$workspace"

        # Verify each result
        for ((i = 0; i < 12; i++)); do
            local week_num
            printf -v week_num "%02d" $((i + 1))
            local expected="${EXPECTED_RESULTS[$i]}"
            local actual="${CHECK_RESULTS[$i]}"
            local expected_line="readme:week-${week_num}: ${expected}"

            if [[ "$actual" != "$expected_line" ]]; then
                echo "FAILED at iteration $iteration, week-${week_num}"
                echo "Expected: '${expected_line}'"
                echo "Actual:   '${actual}'"
                echo "Workspace contents:"
                ls -la "${workspace}/week-${week_num}/"
                return 1
            fi
        done
    done
}
