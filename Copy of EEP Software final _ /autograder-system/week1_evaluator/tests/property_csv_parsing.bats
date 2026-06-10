#!/usr/bin/env bats
# Feature: student-project-verifier, Property 1: CSV parsing preserves all valid IDs
#
# Property 1: For any CSV input containing student IDs separated by commas
# and/or newlines with arbitrary leading/trailing whitespace and empty entries,
# parsing the CSV shall produce exactly the set of non-empty trimmed IDs in the
# order they appear, with no duplicates introduced and no valid IDs lost.
#
# Validates: Requirements 1.4

# Number of random iterations to run
NUM_ITERATIONS=20

setup() {
    TEST_TEMP_DIR="$(mktemp -d)"
    # Extract only the parse_student_ids function from the script (avoid executing main body)
    SCRIPT_DIR="$(cd "$(dirname "${BATS_TEST_FILENAME}")/.." && pwd)"
    SCRIPT_PATH="${SCRIPT_DIR}/verify_projects.sh"
}

teardown() {
    rm -rf "$TEST_TEMP_DIR"
}

# Helper: source only the function definitions from the script, not the main body
# We extract everything up to "# --- Main ---" to get just constants and functions
source_functions() {
    eval "$(sed -n '1,/^# --- Main ---/p' "$SCRIPT_PATH" | head -n -1)"
}

# Helper: generate a random alphanumeric string of given length
random_id() {
    local length="${1:-8}"
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c "$length"
}

# Helper: generate random whitespace (spaces and tabs)
random_whitespace() {
    local max_len="${1:-5}"
    local len=$((RANDOM % (max_len + 1)))
    local ws=""
    for ((i = 0; i < len; i++)); do
        if ((RANDOM % 2 == 0)); then
            ws+=" "
        else
            ws+=$'\t'
        fi
    done
    printf '%s' "$ws"
}

# Helper: generate random CSV content and compute expected IDs
# Sets GENERATED_CSV_FILE and EXPECTED_IDS array
generate_random_csv() {
    EXPECTED_IDS=()
    local csv_content=""
    
    # Decide how many valid IDs to include (1 to 20)
    local num_ids=$((RANDOM % 20 + 1))
    
    # Generate the IDs first
    local ids=()
    for ((i = 0; i < num_ids; i++)); do
        local id_len=$((RANDOM % 12 + 3))  # 3-14 chars
        ids+=("$(random_id "$id_len")")
    done
    
    # Now build CSV content with random separators and whitespace
    local idx=0
    while ((idx < num_ids)); do
        # Decide how many IDs to put on this line (1 to remaining)
        local remaining=$((num_ids - idx))
        local on_this_line=$((RANDOM % remaining + 1))
        if ((on_this_line > 5)); then
            on_this_line=$((RANDOM % 5 + 1))
        fi
        
        local line=""
        for ((j = 0; j < on_this_line && idx < num_ids; j++, idx++)); do
            local id="${ids[$idx]}"
            EXPECTED_IDS+=("$id")
            
            # Add leading whitespace
            local leading
            leading="$(random_whitespace 3)"
            # Add trailing whitespace
            local trailing
            trailing="$(random_whitespace 3)"
            
            if ((j > 0)); then
                # Add comma separator (possibly with extra empty entries)
                local extra_commas=$((RANDOM % 3))
                for ((k = 0; k < extra_commas; k++)); do
                    line+=","
                    # Empty entries between commas don't produce IDs
                    local ws_between
                    ws_between="$(random_whitespace 2)"
                    line+="$ws_between"
                done
                line+=","
            fi
            
            line+="${leading}${id}${trailing}"
        done
        
        # Possibly add trailing commas (empty entries at end of line)
        local trailing_commas=$((RANDOM % 3))
        for ((k = 0; k < trailing_commas; k++)); do
            line+=","
            local ws_trail
            ws_trail="$(random_whitespace 2)"
            line+="$ws_trail"
        done
        
        csv_content+="${line}"$'\n'
        
        # Possibly add blank lines between content lines
        local blank_lines=$((RANDOM % 3))
        for ((k = 0; k < blank_lines; k++)); do
            csv_content+=$'\n'
        done
    done
    
    GENERATED_CSV_FILE="${TEST_TEMP_DIR}/students.csv"
    printf '%s' "$csv_content" > "$GENERATED_CSV_FILE"
}

@test "Property 1: CSV parsing preserves all valid IDs across ${NUM_ITERATIONS} random inputs" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        # Generate random CSV content
        generate_random_csv
        
        # Source the functions and set CSV_FILE
        source_functions
        CSV_FILE="$GENERATED_CSV_FILE"
        
        # Run parse_student_ids
        parse_student_ids
        
        # Verify: same number of IDs
        if [[ ${#STUDENT_IDS[@]} -ne ${#EXPECTED_IDS[@]} ]]; then
            echo "FAILED at iteration $iteration"
            echo "Expected ${#EXPECTED_IDS[@]} IDs, got ${#STUDENT_IDS[@]}"
            echo "CSV content:"
            cat "$GENERATED_CSV_FILE"
            echo "Expected IDs: ${EXPECTED_IDS[*]}"
            echo "Got IDs: ${STUDENT_IDS[*]}"
            return 1
        fi
        
        # Verify: IDs match in order
        for ((i = 0; i < ${#EXPECTED_IDS[@]}; i++)); do
            if [[ "${STUDENT_IDS[$i]}" != "${EXPECTED_IDS[$i]}" ]]; then
                echo "FAILED at iteration $iteration, index $i"
                echo "Expected '${EXPECTED_IDS[$i]}', got '${STUDENT_IDS[$i]}'"
                echo "CSV content:"
                cat "$GENERATED_CSV_FILE"
                echo "Expected IDs: ${EXPECTED_IDS[*]}"
                echo "Got IDs: ${STUDENT_IDS[*]}"
                return 1
            fi
        done
    done
}

@test "Property 1: CSV parsing handles edge case - single ID with heavy whitespace" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        local id
        id="$(random_id $((RANDOM % 10 + 3)))"
        
        # Surround with lots of whitespace and commas
        local leading
        leading="$(random_whitespace 5)"
        local trailing
        trailing="$(random_whitespace 5)"
        local prefix_commas=""
        local suffix_commas=""
        
        local pc=$((RANDOM % 4))
        for ((k = 0; k < pc; k++)); do
            prefix_commas+=","
        done
        local sc=$((RANDOM % 4))
        for ((k = 0; k < sc; k++)); do
            suffix_commas+=","
        done
        
        printf '%s' "${prefix_commas}${leading}${id}${trailing}${suffix_commas}" > "${TEST_TEMP_DIR}/students.csv"
        
        source_functions
        CSV_FILE="${TEST_TEMP_DIR}/students.csv"
        parse_student_ids
        
        if [[ ${#STUDENT_IDS[@]} -ne 1 ]]; then
            echo "FAILED at iteration $iteration: expected 1 ID, got ${#STUDENT_IDS[@]}"
            echo "Input: '$(cat "${TEST_TEMP_DIR}/students.csv")'"
            echo "Got: ${STUDENT_IDS[*]}"
            return 1
        fi
        
        if [[ "${STUDENT_IDS[0]}" != "$id" ]]; then
            echo "FAILED at iteration $iteration: expected '$id', got '${STUDENT_IDS[0]}'"
            echo "Input: '$(cat "${TEST_TEMP_DIR}/students.csv")'"
            return 1
        fi
    done
}

@test "Property 1: CSV parsing produces no IDs from whitespace-only and empty content" {
    for ((iteration = 1; iteration <= NUM_ITERATIONS; iteration++)); do
        # Generate content with only whitespace, commas, and newlines (no valid IDs)
        local content=""
        local num_parts=$((RANDOM % 10 + 1))
        for ((p = 0; p < num_parts; p++)); do
            local choice=$((RANDOM % 3))
            case $choice in
                0) content+="$(random_whitespace 5)" ;;
                1) content+="," ;;
                2) content+=$'\n' ;;
            esac
        done
        
        printf '%s' "$content" > "${TEST_TEMP_DIR}/students.csv"
        
        source_functions
        CSV_FILE="${TEST_TEMP_DIR}/students.csv"
        
        # parse_student_ids exits with error if no IDs found, so we capture that
        run bash -c "
            eval \"\$(sed -n '1,/^# --- Main ---/p' '$SCRIPT_PATH' | head -n -1)\"
            CSV_FILE='${TEST_TEMP_DIR}/students.csv'
            parse_student_ids
        "
        
        # Should exit with non-zero (error: no student IDs found)
        if [[ $status -eq 0 ]]; then
            echo "FAILED at iteration $iteration: expected non-zero exit for empty content"
            echo "Input: '$(cat "${TEST_TEMP_DIR}/students.csv")'"
            return 1
        fi
    done
}
