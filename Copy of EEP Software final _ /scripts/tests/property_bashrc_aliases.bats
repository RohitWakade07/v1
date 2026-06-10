#!/usr/bin/env bats
# Feature: student-project-verifier, Property 4: Bashrc alias detection accuracy
#
# Property 4: For any .bashrc file content containing a random mix of commented
# lines, uncommented alias definitions, non-alias lines, and varying whitespace
# patterns, the alias check shall report PASS if and only if the count of
# uncommented alias definitions (lines matching ^[[:space:]]*alias[[:space:]]+name=...)
# is at least 2.
#
# Validates: Requirements 4.1, 4.2, 4.3

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

# Helper: generate a random valid alias name
random_alias_name() {
    local first_chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    local rest_chars="abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    local len=$((RANDOM % 8 + 1))
    local name=""
    # First character must be [a-zA-Z_]
    local idx=$((RANDOM % ${#first_chars}))
    name="${first_chars:$idx:1}"
    # Remaining characters
    for ((c = 1; c < len; c++)); do
        idx=$((RANDOM % ${#rest_chars}))
        name="${name}${rest_chars:$idx:1}"
    done
    echo "$name"
}

# Helper: generate random leading whitespace (spaces and tabs)
random_whitespace() {
    local len=$((RANDOM % 4))
    local ws=""
    for ((i = 0; i < len; i++)); do
        if ((RANDOM % 2 == 0)); then
            ws="${ws} "
        else
            ws="${ws}	"
        fi
    done
    echo "$ws"
}

# Helper: generate a random alias value
random_alias_value() {
    local values=("'ls -la'" "'cd ~'" "\"grep -r\"" "'echo hello'" "\"pwd\"" "'cat /dev/null'" "~/.local/bin/foo" "/usr/bin/bar")
    local idx=$((RANDOM % ${#values[@]}))
    echo "${values[$idx]}"
}

# Helper: generate a random non-alias line
random_non_alias_line() {
    local lines=(
        "export PATH=\$PATH:/usr/local/bin"
        "# This is a comment"
        ""
        "echo \"Hello World\""
        "source ~/.bash_profile"
        "PS1='\\u@\\h:\\w\\$ '"
        "if [ -f ~/.bash_aliases ]; then"
        "fi"
        "export EDITOR=vim"
        "umask 022"
        "shopt -s histappend"
    )
    local idx=$((RANDOM % ${#lines[@]}))
    echo "${lines[$idx]}"
}

# Helper: generate random .bashrc content and track expected uncommented alias count
# Sets UNCOMMENTED_ALIAS_COUNT with the number of valid uncommented aliases
generate_random_bashrc() {
    local output_file="$1"
    local num_uncommented=$((RANDOM % 5))
    local num_commented=$((RANDOM % 4))
    local num_non_alias=$((RANDOM % 6 + 1))

    UNCOMMENTED_ALIAS_COUNT=$num_uncommented

    # Build lines array
    local lines=()

    # Add uncommented alias lines with varying whitespace
    for ((i = 0; i < num_uncommented; i++)); do
        local ws
        ws="$(random_whitespace)"
        local name
        name="$(random_alias_name)"
        local value
        value="$(random_alias_value)"
        lines+=("${ws}alias ${name}=${value}")
    done

    # Add commented alias lines (should NOT count)
    for ((i = 0; i < num_commented; i++)); do
        local ws
        ws="$(random_whitespace)"
        local name
        name="$(random_alias_name)"
        local value
        value="$(random_alias_value)"
        lines+=("${ws}# alias ${name}=${value}")
    done

    # Add non-alias lines
    for ((i = 0; i < num_non_alias; i++)); do
        lines+=("$(random_non_alias_line)")
    done

    # Shuffle lines by writing to temp file and using shuf
    printf '%s\n' "${lines[@]}" | shuf > "$output_file"
}

@test "Property 4: Bashrc alias detection accuracy across ${NUM_ITERATIONS} random .bashrc files" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        # Create isolated home directory for this iteration
        local home_dir="${TEST_TEMP_DIR}/iter_${iteration}/home"
        mkdir -p "$home_dir"

        # Generate random .bashrc content
        generate_random_bashrc "${home_dir}/.bashrc"

        # Source functions and run verify_bashrc
        source_functions
        CHECK_RESULTS=()
        verify_bashrc "$home_dir"

        # Determine expected result
        local expected
        if [[ $UNCOMMENTED_ALIAS_COUNT -ge 2 ]]; then
            expected="bashrc: PASS"
        else
            expected="bashrc: FAIL"
        fi

        # Verify result
        if [[ ${#CHECK_RESULTS[@]} -ne 1 ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected 1 result, got ${#CHECK_RESULTS[@]}"
            echo "Results: ${CHECK_RESULTS[*]}"
            echo "Bashrc content:"
            cat "${home_dir}/.bashrc"
            return 1
        fi

        if [[ "${CHECK_RESULTS[0]}" != "$expected" ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected: '${expected}'"
            echo "Actual:   '${CHECK_RESULTS[0]}'"
            echo "Uncommented alias count: $UNCOMMENTED_ALIAS_COUNT"
            echo "Bashrc content:"
            cat "${home_dir}/.bashrc"
            return 1
        fi
    done
}

@test "Property 4: Bashrc alias detection with varying whitespace patterns" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local home_dir="${TEST_TEMP_DIR}/ws_${iteration}/home"
        mkdir -p "$home_dir"

        # Generate aliases with specific whitespace variations
        local num_aliases=$((RANDOM % 5))
        UNCOMMENTED_ALIAS_COUNT=$num_aliases
        local bashrc_file="${home_dir}/.bashrc"
        > "$bashrc_file"

        for ((i = 0; i < num_aliases; i++)); do
            local name
            name="$(random_alias_name)"
            local value
            value="$(random_alias_value)"
            # Vary whitespace between alias keyword and name
            local leading_ws=""
            local mid_ws=" "
            local ws_choice=$((RANDOM % 4))
            case $ws_choice in
                0) leading_ws="" ; mid_ws=" " ;;
                1) leading_ws="  " ; mid_ws=" " ;;
                2) leading_ws="	" ; mid_ws="  " ;;
                3) leading_ws="	  " ; mid_ws="	" ;;
            esac
            echo "${leading_ws}alias${mid_ws}${name}=${value}" >> "$bashrc_file"
        done

        # Add some non-alias lines
        echo "export FOO=bar" >> "$bashrc_file"
        echo "# just a comment" >> "$bashrc_file"

        # Source functions and run verify_bashrc
        source_functions
        CHECK_RESULTS=()
        verify_bashrc "$home_dir"

        # Determine expected result
        local expected
        if [[ $UNCOMMENTED_ALIAS_COUNT -ge 2 ]]; then
            expected="bashrc: PASS"
        else
            expected="bashrc: FAIL"
        fi

        if [[ "${CHECK_RESULTS[0]}" != "$expected" ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected: '${expected}'"
            echo "Actual:   '${CHECK_RESULTS[0]}'"
            echo "Uncommented alias count: $UNCOMMENTED_ALIAS_COUNT"
            echo "Bashrc content:"
            cat "$bashrc_file"
            return 1
        fi
    done
}

@test "Property 4: Missing .bashrc always results in FAIL" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local home_dir="${TEST_TEMP_DIR}/missing_${iteration}/home"
        mkdir -p "$home_dir"
        # Do NOT create .bashrc

        # Source functions and run verify_bashrc
        source_functions
        CHECK_RESULTS=()
        verify_bashrc "$home_dir"

        if [[ "${CHECK_RESULTS[0]}" != "bashrc: FAIL" ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected: 'bashrc: FAIL'"
            echo "Actual:   '${CHECK_RESULTS[0]}'"
            echo "Home dir contents:"
            ls -la "$home_dir"
            return 1
        fi
    done
}
