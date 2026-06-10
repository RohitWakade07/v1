#!/usr/bin/env bash
#
# verify_projects.sh - Automated verification of student EEP Software project submissions
#
# Usage: ./verify_projects.sh <csv_file> [--students-db <students_csv>]
#
# Description:
#   Reads student IDs from a CSV file, verifies each student's workspace
#   against EEP Software course requirements, and generates individual
#   pass/fail report files in the current working directory.
#
#   When --students-db is provided, the script prompts for a student ID,
#   looks up the student's name, generates a SHA-256 hash for identity
#   verification, and embeds the hash in the report file. A hashed CSV
#   (students_hashed.csv) is also written to the current directory.
#
# Arguments:
#   <csv_file>              Path to a CSV file containing student IDs
#   --students-db <file>    Optional: path to students CSV (Student_ID,Name)
#                           Enables hash-based identity verification
#
# Output:
#   For each student ID, creates a report file named [ID]_EEP1_Week1
#   in the current working directory containing pass/fail results.
#   When --students-db is used, also writes students_hashed.csv.
#
# Checks performed per student:
#   - Directory structure: week-01..week-12, notes, scripts, capstone
#   - README.md presence in each week-XX folder
#   - At least 2 alias definitions in ~/.bashrc
#   - workspace-report.txt exists in ~/eep-software/
#
# Exit codes:
#   0 - Successful completion (even if individual students fail checks)
#   1 - Invalid arguments or missing/empty CSV file
#
# Note: The "grader system" folder is explicitly excluded from all checks.
# Make executable: chmod +x verify_projects.sh
#

# --- Constants ---
REQUIRED_DIRS=(week-01 week-02 week-03 week-04 week-05 week-06 week-07 week-08 week-09 week-10 week-11 week-12 notes scripts capstone)
EXCLUDED_DIRS=("grader system")
MIN_ALIASES=2
WORKSPACE_DIR="$HOME/eep-software"

# Hash-verification globals (populated when --students-db is used)
STUDENTS_DB=""
VERIFIED_STUDENT_ID=""
VERIFIED_STUDENT_NAME=""
VERIFIED_STUDENT_HASH=""

# --- Functions ---

# validate_args: Validates command-line arguments
# Accepts: <csv_file> [--students-db <students_csv>]
# Sets CSV_FILE and optionally STUDENTS_DB; exits with error on failure
validate_args() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: verify_projects.sh <csv_file> [--students-db <students_csv>]" >&2
        exit 1
    fi

    # Parse arguments
    CSV_FILE=""
    STUDENTS_DB=""
    local positional=()

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --students-db)
                if [[ -z "${2:-}" ]]; then
                    echo "Error: --students-db requires a file argument" >&2
                    exit 1
                fi
                STUDENTS_DB="$2"
                shift 2
                ;;
            -*)
                echo "Error: unknown option: $1" >&2
                echo "Usage: verify_projects.sh <csv_file> [--students-db <students_csv>]" >&2
                exit 1
                ;;
            *)
                positional+=("$1")
                shift
                ;;
        esac
    done

    if [[ ${#positional[@]} -ne 1 ]]; then
        echo "Usage: verify_projects.sh <csv_file> [--students-db <students_csv>]" >&2
        exit 1
    fi

    CSV_FILE="${positional[0]}"

    if [[ ! -f "$CSV_FILE" ]]; then
        echo "Error: file not found: $CSV_FILE" >&2
        exit 1
    fi

    if [[ -n "$STUDENTS_DB" && ! -f "$STUDENTS_DB" ]]; then
        echo "Error: students database not found: $STUDENTS_DB" >&2
        exit 1
    fi
}

# parse_student_ids: Reads the CSV file and extracts student IDs
# Splits on commas and newlines, trims whitespace, skips empty entries
# Populates the STUDENT_IDS array
# Exits with error if no valid IDs found after parsing
parse_student_ids() {
    STUDENT_IDS=()

    while IFS= read -r line || [[ -n "$line" ]]; do
        # Split line on commas
        IFS=',' read -ra tokens <<< "$line"
        for token in "${tokens[@]}"; do
            # Trim leading and trailing whitespace
            trimmed="$(echo "$token" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
            # Skip empty entries
            if [[ -n "$trimmed" ]]; then
                STUDENT_IDS+=("$trimmed")
            fi
        done
    done < "$CSV_FILE"

    if [[ ${#STUDENT_IDS[@]} -eq 0 ]]; then
        echo "Error: no student IDs found in $CSV_FILE" >&2
        exit 1
    fi
}

# verify_directories: Verifies required directory structure exists in student workspace
# Input: $1 = workspace path
# Output: Appends results to CHECK_RESULTS array in format "dir:<name>: PASS" or "dir:<name>: FAIL"
verify_directories() {
    local workspace="$1"

    # If workspace root doesn't exist, mark all directory checks FAIL and return
    if [[ ! -d "$workspace" ]]; then
        for dir in "${REQUIRED_DIRS[@]}"; do
            CHECK_RESULTS+=("dir:${dir}: FAIL")
        done
        return
    fi

    # Verify each required directory
    for dir in "${REQUIRED_DIRS[@]}"; do
        # Explicitly skip excluded directories (e.g., "grader system")
        local skip=false
        for excluded in "${EXCLUDED_DIRS[@]}"; do
            if [[ "$dir" == "$excluded" ]]; then
                skip=true
                break
            fi
        done
        if [[ "$skip" == true ]]; then
            continue
        fi

        # Check if the directory exists as an actual directory (not a file)
        if [[ -d "${workspace}/${dir}" ]]; then
            CHECK_RESULTS+=("dir:${dir}: PASS")
        else
            CHECK_RESULTS+=("dir:${dir}: FAIL")
        fi
    done
}

# verify_readmes: Checks that each weekly folder contains a README.md file
# Accepts workspace path as argument
# Appends results to CHECK_RESULTS array with format "readme:week-XX: PASS/FAIL"
verify_readmes() {
    local workspace="$1"

    for week_num in $(seq -w 1 12); do
        local week_dir="week-${week_num}"
        local readme_path="${workspace}/${week_dir}/README.md"

        if [[ -f "$readme_path" ]]; then
            CHECK_RESULTS+=("readme:${week_dir}: PASS")
        else
            CHECK_RESULTS+=("readme:${week_dir}: FAIL")
        fi
    done
}

# verify_bashrc: Checks that the student's .bashrc contains at least MIN_ALIASES alias definitions
# Arguments: $1 - student home directory path
# Appends "bashrc: PASS" or "bashrc: FAIL" to CHECK_RESULTS
verify_bashrc() {
    local home_dir="$1"
    local bashrc_file="$home_dir/.bashrc"

    if [[ ! -f "$bashrc_file" ]]; then
        CHECK_RESULTS+=("bashrc: FAIL")
        return
    fi

    local alias_count
    alias_count=$(grep -c '^[[:space:]]*alias[[:space:]]\+[a-zA-Z_][a-zA-Z0-9_]*=' "$bashrc_file" 2>/dev/null || echo "0")

    if [[ "$alias_count" -ge "$MIN_ALIASES" ]]; then
        CHECK_RESULTS+=("bashrc: PASS")
    else
        CHECK_RESULTS+=("bashrc: FAIL")
    fi
}

# verify_workspace_report: Verifies workspace-report.txt exists in student workspace
# Input: $1 = workspace path
# Output: Appends result to CHECK_RESULTS array as "workspace-report: PASS" or "workspace-report: FAIL"
verify_workspace_report() {
    local workspace="$1"

    if [[ -f "${workspace}/workspace-report.txt" ]]; then
        CHECK_RESULTS+=("workspace-report: PASS")
    else
        CHECK_RESULTS+=("workspace-report: FAIL")
    fi
}

# generate_report: Generates a pass/fail report file for a student
# Arguments: $1 - student ID
# Uses global CHECK_RESULTS array containing entries like "check_name: PASS" or "check_name: FAIL"
# Uses VERIFIED_STUDENT_HASH and VERIFIED_STUDENT_NAME if set (hash-verification mode)
# Output: File named [ID]_EEP1_Week1 in current working directory (overwrites if exists)
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
        # Embed identity info if hash-verification mode is active
        if [[ -n "$VERIFIED_STUDENT_HASH" && "$student_id" == "$VERIFIED_STUDENT_ID" ]]; then
            echo "Name: $VERIFIED_STUDENT_NAME"
            echo "Hash: $VERIFIED_STUDENT_HASH"
        fi
        for result in "${CHECK_RESULTS[@]}"; do
            echo "$result"
        done
        echo "Overall: $overall"
    } > "$report_file"
}

# --- Hash verification functions ---

# generate_student_hash: Produces a deterministic SHA-256 hash from a student ID
# Arguments: $1 - student ID
# Output: prints the hex hash string
generate_student_hash() {
    echo -n "$1" | sha256sum | awk '{print $1}'
}

# lookup_student: Finds a student's name in the students DB CSV
# Arguments: $1 - student ID, $2 - path to students CSV
# Sets VERIFIED_STUDENT_NAME; returns 1 if not found
lookup_student() {
    local target_id="$1"
    local db_file="$2"
    local first=true

    while IFS=',' read -r sid name; do
        # Skip header
        if [[ "$first" == true ]]; then
            first=false
            continue
        fi
        sid="$(echo "$sid" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        name="$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        if [[ "$sid" == "$target_id" ]]; then
            VERIFIED_STUDENT_NAME="$name"
            return 0
        fi
    done < "$db_file"

    return 1
}

# prompt_student_identity: Interactively asks for a student ID, validates it,
# generates a hash, and writes students_hashed.csv
# Uses global STUDENTS_DB
prompt_student_identity() {
    echo ""
    echo "=== Student Identity Verification ==="
    read -rp "Enter your Student ID: " input_id

    input_id="$(echo "$input_id" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

    if [[ -z "$input_id" ]]; then
        echo "Error: no Student ID entered." >&2
        exit 1
    fi

    if ! lookup_student "$input_id" "$STUDENTS_DB"; then
        echo "Error: Student ID '$input_id' not found in $STUDENTS_DB" >&2
        exit 1
    fi

    VERIFIED_STUDENT_ID="$input_id"
    VERIFIED_STUDENT_HASH="$(generate_student_hash "$input_id")"

    echo "Identity confirmed: $VERIFIED_STUDENT_NAME ($VERIFIED_STUDENT_ID)"
    echo "Hash: $VERIFIED_STUDENT_HASH"
    echo ""

    # Write students_hashed.csv with all students + hashes
    write_hashed_csv
}

# write_hashed_csv: Reads STUDENTS_DB, computes hashes for all students,
# and writes students_hashed.csv to the current working directory
write_hashed_csv() {
    local output="students_hashed.csv"
    echo "Student_ID,Name,Hash" > "$output"

    local first=true
    while IFS=',' read -r sid name; do
        if [[ "$first" == true ]]; then
            first=false
            continue
        fi
        sid="$(echo "$sid" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        name="$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [[ -z "$sid" ]] && continue
        local h
        h="$(generate_student_hash "$sid")"
        echo "${sid},${name},${h}" >> "$output"
    done < "$STUDENTS_DB"

    echo "Written: $output"
}

# --- Main ---
validate_args "$@"
parse_student_ids

# If a students database was provided, prompt for identity and generate hash
if [[ -n "$STUDENTS_DB" ]]; then
    prompt_student_identity
fi

# Process each student
for student_id in "${STUDENT_IDS[@]}"; do
    # Resolve home directory and workspace path
    home_dir="/home/${student_id}"
    workspace="${home_dir}/eep-software"

    # Initialize check results for this student
    CHECK_RESULTS=()

    # Run all verification functions, handling errors gracefully
    if ! verify_directories "$workspace" 2>/dev/null; then
        echo "Error: failed to verify directories for ${student_id}" >&2
        continue
    fi

    if ! verify_readmes "$workspace" 2>/dev/null; then
        echo "Error: failed to verify READMEs for ${student_id}" >&2
        continue
    fi

    if ! verify_bashrc "$home_dir" 2>/dev/null; then
        echo "Error: failed to verify .bashrc for ${student_id}" >&2
        continue
    fi

    if ! verify_workspace_report "$workspace" 2>/dev/null; then
        echo "Error: failed to verify workspace report for ${student_id}" >&2
        continue
    fi

    # Generate the report for this student
    if ! generate_report "$student_id" 2>/dev/null; then
        echo "Error: failed to generate report for ${student_id}" >&2
        continue
    fi
done

exit 0
