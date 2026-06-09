#!/bin/bash
# EEP3 Week 3 Project Verifier — File Organizer
# Generates random test files, runs student's organize.sh against them,
# verifies files are sorted correctly.
#
# DO NOT MODIFY THIS SCRIPT.

set -uo pipefail

PUBLIC_KEY='-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApYmNjG2L7Ci4MLlkGmAh
gbzdFNBpaF6dDfcilzfE8n77Y0tPJclieRdlqjBp4mV5nZWJt6HkI/wbGLir7n6E
tx6odtUikrEbkcgYmQ2Ey+MygkxgaEUqJjCow+Sp0tluwnu0Ul/IupUeptDD3xcH
t4oEXadeCozB5W1U4hqlU24VW2O/RIs++ggY78H7fAez/3KFlwL7+Nc2n+RqotEI
xP3k2OH7Ko8YjSS1CdbzOPsQXaCqXwlUN/bxDZca2te6rlogjUw2zkWh8MvH821Z
VBSgsKerVguUmaONJo3UZjqJQ9pBKhOWX84vrKwyHlIXe8JOnIdZTJlk+14xw27Z
bQIDAQAB
-----END PUBLIC KEY-----'

WORKSPACE="$HOME/eep-software/week-03"
SCRIPT="$WORKSPACE/organize.sh"

API_BASE_URL="${EEP_API_BASE_URL:-http://localhost:5173}"
ASSIGNMENT_SLUG="${EEP_ASSIGNMENT_SLUG:-eep-week3}"
EVALUATOR_KEY="${EEP_EVALUATOR_KEY:-}"
STUDENT_TOKEN="${EEP_STUDENT_TOKEN:-}"
AUTO_UPLOAD="${EEP_AUTO_UPLOAD:-0}"
AUTO_LOGIN="${EEP_AUTO_LOGIN:-0}"
STUDENT_PASSWORD="${EEP_STUDENT_PASSWORD:-}"

trim() { echo "$1" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }

start_evaluator_session() {
    if [[ -z "$EVALUATOR_KEY" ]]; then
        echo "[warn] EEP_EVALUATOR_KEY is not set; skipping session bootstrap."
        return
    fi
    if ! command -v curl >/dev/null 2>&1; then
        echo "[warn] curl not found; skipping session bootstrap."
        return
    fi

    local payload
    payload=$(printf '{"student_roll":"%s","assignment_slug":"%s"}' "$STUDENT_ID" "$ASSIGNMENT_SLUG")
    local response
    response=$(curl -s -X POST "${API_BASE_URL}/api/v1/sessions/start-evaluator" \
        -H "Content-Type: application/json" \
        -H "X-Evaluator-Key: ${EVALUATOR_KEY}" \
        -d "$payload")
    echo "[info] Session bootstrap response: $response"

    if command -v python3 >/dev/null 2>&1; then
        export EEP_SESSION_RESPONSE="$response"
        SESSION_ID=$(python3 - <<'PY'
import json
import os
import sys

data = os.environ.get("EEP_SESSION_RESPONSE", "")
try:
    payload = json.loads(data)
    print(payload.get("session_id", "") or "")
except Exception:
    sys.stderr.write("[warn] Could not parse JSON from evaluator bootstrap response.\n")
    sys.exit(1)
PY
        )
        unset EEP_SESSION_RESPONSE
    else
        SESSION_ID=$(echo "$response" | sed -n 's/.*"session_id":"\([^"]*\)".*/\1/p')
    fi

    if [[ -z "${SESSION_ID:-}" ]]; then
        echo "[warn] Could not extract session_id; evaluator bootstrap may have failed."
    fi
}

authenticate_student_early() {
    if [[ "$AUTO_LOGIN" != "1" ]]; then
        return
    fi
    if ! command -v curl >/dev/null 2>&1; then
        echo "[warn] curl not found; skipping login validation."
        return
    fi

    if [[ -z "${STUDENT_PASSWORD:-}" ]]; then
        read -rsp "Enter student password for ${STUDENT_ID}: " STUDENT_PASSWORD
        echo ""
    fi

    echo "Authenticating student..."
    local login_resp
    login_resp=$(curl -s -X POST "${API_BASE_URL}/api/v1/auth/student/login" \
        -H "Content-Type: application/json" \
        -d "{\"roll_number\":\"${STUDENT_ID}\",\"password\":\"${STUDENT_PASSWORD}\"}")

    STUDENT_TOKEN=$(echo "$login_resp" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')

    if [[ -z "${STUDENT_TOKEN:-}" ]]; then
        local error_msg
        error_msg=$(echo "$login_resp" | sed -n 's/.*"detail":"\([^"]*\)".*/\1/p')
        [[ -z "$error_msg" ]] && error_msg="Authentication failed. Please check your credentials."
        echo "Error: $error_msg" >&2
        exit 1
    fi
    echo "Authentication successful."
}

upload_report_file() {
    if [[ "$AUTO_UPLOAD" != "1" ]]; then
        return
    fi
    if [[ -z "$STUDENT_TOKEN" ]]; then
        echo "[warn] EEP_STUDENT_TOKEN is not set; skipping auto-upload."
        return
    fi
    if [[ -z "${SESSION_ID:-}" ]]; then
        echo "[warn] session_id missing; skipping auto-upload."
        return
    fi
    if ! command -v curl >/dev/null 2>&1; then
        echo "[warn] curl not found; skipping auto-upload."
        return
    fi

    local upload_resp
    upload_resp=$(curl -s -X POST "${API_BASE_URL}/api/v1/sessions/${SESSION_ID}/payload" \
        -H "Authorization: Bearer ${STUDENT_TOKEN}" \
        -F "file=@${OUTPUT_FILE}")
    echo "[info] Auto-upload response: $upload_resp"
}

RESULTS=()
add_check() { RESULTS+=("$1: $2"); }

# ── Generate random test files ────────────────────────────────────────────────
DOC_EXTS=("txt" "pdf" "doc" "docx")
IMG_EXTS=("jpg" "jpeg" "png" "gif" "bmp")
CODE_EXTS=("py" "sh" "js" "c" "cpp")
OTHER_EXTS=("csv" "yml" "zip" "mp3" "dat" "bin" "xml" "log")

random_name() {
    head -c 100 /dev/urandom | tr -dc 'a-z0-9' | head -c $((RANDOM % 8 + 4)) || true
}

generate_test_folder() {
    local testdir="$1"
    rm -rf "$testdir"
    mkdir -p "$testdir"

    EXPECTED_DOCS=0
    EXPECTED_IMGS=0
    EXPECTED_CODE=0
    EXPECTED_OTHER=0
    TOTAL_FILES=0

    # Generate 15-25 random files
    local count=$((RANDOM % 11 + 15))
    for ((i=0; i<count; i++)); do
        local category=$((RANDOM % 4))
        local name=$(random_name)
        local ext=""
        case $category in
            0)
                ext="${DOC_EXTS[$((RANDOM % ${#DOC_EXTS[@]}))]}"
                ((EXPECTED_DOCS++))
                ;;
            1)
                ext="${IMG_EXTS[$((RANDOM % ${#IMG_EXTS[@]}))]}"
                ((EXPECTED_IMGS++))
                ;;
            2)
                ext="${CODE_EXTS[$((RANDOM % ${#CODE_EXTS[@]}))]}"
                ((EXPECTED_CODE++))
                ;;
            3)
                ext="${OTHER_EXTS[$((RANDOM % ${#OTHER_EXTS[@]}))]}"
                ((EXPECTED_OTHER++))
                ;;
        esac
        touch "$testdir/${name}.${ext}"
        ((TOTAL_FILES++))
    done
}

# ── Checks ────────────────────────────────────────────────────────────────────

check_files_exist() {
    [[ -d "$WORKSPACE" ]] && add_check "dir:week-03" "PASS" || add_check "dir:week-03" "FAIL"
    [[ -f "$SCRIPT" ]] && add_check "file:organize.sh" "PASS" || add_check "file:organize.sh" "FAIL"
    [[ -x "$SCRIPT" ]] && add_check "executable:organize.sh" "PASS" || add_check "executable:organize.sh" "FAIL"
}

check_input_validation() {
    if [[ ! -f "$SCRIPT" || ! -x "$SCRIPT" ]]; then
        add_check "validation:no_args" "FAIL"
        add_check "validation:bad_dir" "FAIL"
        return
    fi
    # Test no arguments
    if bash "$SCRIPT" >/dev/null 2>&1; then
        add_check "validation:no_args" "FAIL"
    else
        add_check "validation:no_args" "PASS"
    fi
    # Test invalid directory
    if bash "$SCRIPT" "/tmp/nonexistent_dir_xyz_$$" >/dev/null 2>&1; then
        add_check "validation:bad_dir" "FAIL"
    else
        add_check "validation:bad_dir" "PASS"
    fi
}

check_organization() {
    if [[ ! -f "$SCRIPT" || ! -x "$SCRIPT" ]]; then
        add_check "org:creates_folders" "FAIL"
        add_check "org:documents_correct" "FAIL"
        add_check "org:images_correct" "FAIL"
        add_check "org:code_correct" "FAIL"
        add_check "org:other_correct" "FAIL"
        add_check "org:no_files_left" "FAIL"
        add_check "org:summary_output" "FAIL"
        return
    fi

    local testdir
    testdir=$(mktemp -d)
    generate_test_folder "$testdir"

    # Run student's script
    local output
    output=$(bash "$SCRIPT" "$testdir" 2>&1) || true

    # Check sub-folders created
    if [[ -d "$testdir/Documents" && -d "$testdir/Images" && -d "$testdir/Code" && -d "$testdir/Other" ]]; then
        add_check "org:creates_folders" "PASS"
    else
        add_check "org:creates_folders" "FAIL"
    fi

    # Count files in each folder
    local actual_docs actual_imgs actual_code actual_other
    actual_docs=$(find "$testdir/Documents" -maxdepth 1 -type f 2>/dev/null | wc -l)
    actual_imgs=$(find "$testdir/Images" -maxdepth 1 -type f 2>/dev/null | wc -l)
    actual_code=$(find "$testdir/Code" -maxdepth 1 -type f 2>/dev/null | wc -l)
    actual_other=$(find "$testdir/Other" -maxdepth 1 -type f 2>/dev/null | wc -l)

    # Verify counts match expected
    [[ "$actual_docs" -eq "$EXPECTED_DOCS" ]] && add_check "org:documents_correct" "PASS" || add_check "org:documents_correct" "FAIL"
    [[ "$actual_imgs" -eq "$EXPECTED_IMGS" ]] && add_check "org:images_correct" "PASS" || add_check "org:images_correct" "FAIL"
    [[ "$actual_code" -eq "$EXPECTED_CODE" ]] && add_check "org:code_correct" "PASS" || add_check "org:code_correct" "FAIL"
    [[ "$actual_other" -eq "$EXPECTED_OTHER" ]] && add_check "org:other_correct" "PASS" || add_check "org:other_correct" "FAIL"

    # Check no files remain in root (only directories should remain)
    local leftover
    leftover=$(find "$testdir" -maxdepth 1 -type f | wc -l)
    [[ "$leftover" -eq 0 ]] && add_check "org:no_files_left" "PASS" || add_check "org:no_files_left" "FAIL"

    # Check summary output exists
    if echo "$output" | grep -qiE '(summary|document|image|code|other|total|moved)'; then
        add_check "org:summary_output" "PASS"
    else
        add_check "org:summary_output" "FAIL"
    fi

    rm -rf "$testdir"
}

check_techniques() {
    if [[ ! -f "$SCRIPT" ]]; then
        add_check "technique:conditionals" "FAIL"
        add_check "technique:loop" "FAIL"
        return
    fi
    # Check uses conditionals (if/elif/case)
    if grep -qE '(if \[|elif|case )' "$SCRIPT"; then
        add_check "technique:conditionals" "PASS"
    else
        add_check "technique:conditionals" "FAIL"
    fi
    # Check uses a loop (for/while)
    if grep -qE '(for |while )' "$SCRIPT"; then
        add_check "technique:loop" "PASS"
    else
        add_check "technique:loop" "FAIL"
    fi
}

# ── Encryption ────────────────────────────────────────────────────────────────
encrypt_report() {
    local plaintext="$1" outfile="$2"
    local tmpkey tmplain tmpaes_key tmpaes_enc tmpenc_key
    tmpkey=$(mktemp); tmplain=$(mktemp); tmpaes_key=$(mktemp)
    tmpaes_enc=$(mktemp); tmpenc_key=$(mktemp)
    echo "$PUBLIC_KEY" > "$tmpkey"
    echo -n "$plaintext" > "$tmplain"
    openssl rand 32 > "$tmpaes_key"
    openssl enc -aes-256-cbc -pbkdf2 -pass file:"$tmpaes_key" -in "$tmplain" -out "$tmpaes_enc" 2>/dev/null
    openssl rsautl -encrypt -pubin -inkey "$tmpkey" -in "$tmpaes_key" -out "$tmpenc_key" 2>/dev/null
    echo "$(base64 -w 0 < "$tmpenc_key"):$(base64 -w 0 < "$tmpaes_enc")" > "$outfile"
    rm -f "$tmpkey" "$tmplain" "$tmpaes_key" "$tmpaes_enc" "$tmpenc_key"
}

# ── Main ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  EEP Software — Week 3 Project Verifier  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if [[ -z "${STUDENT_ID:-}" ]]; then
    read -rp "Enter your Student ID: " RAW_ID
    STUDENT_ID="$(trim "$RAW_ID")"
fi
[[ -z "$STUDENT_ID" ]] && echo "Error: Student ID cannot be empty." >&2 && exit 1

authenticate_student_early

echo ""
echo "Verifying Week 3 assignment for: $STUDENT_ID"
echo "Testing with randomly generated files..."
echo ""

start_evaluator_session

check_files_exist
check_input_validation
check_organization
check_techniques

OVERALL="PASS"
for r in "${RESULTS[@]}"; do [[ "$r" == *": FAIL" ]] && OVERALL="FAIL" && break; done

for r in "${RESULTS[@]}"; do
    [[ "$r" == *": PASS" ]] && echo "  ✓ $r" || echo "  ✗ $r"
done
echo ""
echo "Overall: $OVERALL"
echo ""

TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
REPORT_BODY="STUDENT_ID: ${STUDENT_ID}
TIMESTAMP: ${TIMESTAMP}
WEEK: 3
"
for r in "${RESULTS[@]}"; do REPORT_BODY+="${r}
"; done
REPORT_BODY+="Overall: ${OVERALL}"

OUTPUT_FILE="${STUDENT_ID}_EEP3_Week3.eep3"
encrypt_report "$REPORT_BODY" "$OUTPUT_FILE"

upload_report_file

echo "Report written to: $OUTPUT_FILE"
echo "Upload this file to the course website."
echo ""
