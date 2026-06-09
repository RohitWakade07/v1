#!/bin/bash
# EEP1 Week 1 Project Verifier
# Students run this on their Linux machine.
#
# What it does:
#   1. Prompts for Student ID
#   2. Checks ~/eep-software/ workspace
#   3. Encrypts the report with the instructor's public key (RSA+AES hybrid)
#   4. Writes an opaque .eep1 file — student cannot read or tamper with it
#   5. Student uploads the file to the course website
#
# DO NOT MODIFY THIS SCRIPT.

set -euo pipefail

# ---------------------------------------------------------------
# Instructor's RSA public key (embedded — students cannot decrypt)
# Replace this with your own public key from keys/instructor_public.pem
# ---------------------------------------------------------------
PUBLIC_KEY='-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApYmNjG2L7Ci4MLlkGmAh
gbzdFNBpaF6dDfcilzfE8n77Y0tPJclieRdlqjBp4mV5nZWJt6HkI/wbGLir7n6E
tx6odtUikrEbkcgYmQ2Ey+MygkxgaEUqJjCow+Sp0tluwnu0Ul/IupUeptDD3xcH
t4oEXadeCozB5W1U4hqlU24VW2O/RIs++ggY78H7fAez/3KFlwL7+Nc2n+RqotEI
xP3k2OH7Ko8YjSS1CdbzOPsQXaCqXwlUN/bxDZca2te6rlogjUw2zkWh8MvH821Z
VBSgsKerVguUmaONJo3UZjqJQ9pBKhOWX84vrKwyHlIXe8JOnIdZTJlk+14xw27Z
bQIDAQAB
-----END PUBLIC KEY-----'

# ---------------------------------------------------------------
# Constants
# ---------------------------------------------------------------
REQUIRED_DIRS=(week-01 week-02 week-03 week-04 week-05 week-06
               week-07 week-08 week-09 week-10 week-11 week-12
               notes scripts capstone)
EXCLUDED_DIRS=("grader system")
MIN_ALIASES=2
WORKSPACE="$HOME/eep-software"
API_BASE_URL="${EEP_API_BASE_URL:-http://localhost:5173}"
ASSIGNMENT_SLUG="${EEP_ASSIGNMENT_SLUG:-eep-week1}"
EVALUATOR_KEY="${EEP_EVALUATOR_KEY:-}"
STUDENT_TOKEN="${EEP_STUDENT_TOKEN:-}"
AUTO_UPLOAD="${EEP_AUTO_UPLOAD:-0}"
AUTO_LOGIN="${EEP_AUTO_LOGIN:-0}"
STUDENT_PASSWORD="${EEP_STUDENT_PASSWORD:-}"

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
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

# ---------------------------------------------------------------
# Verification functions
# ---------------------------------------------------------------
verify_directories() {
    if [[ ! -d "$WORKSPACE" ]]; then
        for d in "${REQUIRED_DIRS[@]}"; do RESULTS+=("dir:${d}: FAIL"); done
        return
    fi
    for d in "${REQUIRED_DIRS[@]}"; do
        local skip=false
        for ex in "${EXCLUDED_DIRS[@]}"; do [[ "$d" == "$ex" ]] && skip=true && break; done
        $skip && continue
        [[ -d "${WORKSPACE}/${d}" ]] && RESULTS+=("dir:${d}: PASS") || RESULTS+=("dir:${d}: FAIL")
    done
}

verify_readmes() {
    for n in $(seq -w 1 12); do
        [[ -f "${WORKSPACE}/week-${n}/README.md" ]] \
            && RESULTS+=("readme:week-${n}: PASS") \
            || RESULTS+=("readme:week-${n}: FAIL")
    done
}

verify_bashrc() {
    local bashrc="$HOME/.bashrc"
    if [[ ! -f "$bashrc" ]]; then RESULTS+=("bashrc: FAIL"); return; fi
    local count
    count=$(grep -c '^[[:space:]]*alias[[:space:]]\+[a-zA-Z_][a-zA-Z0-9_]*=' "$bashrc" 2>/dev/null || echo 0)
    [[ "$count" -ge "$MIN_ALIASES" ]] && RESULTS+=("bashrc: PASS") || RESULTS+=("bashrc: FAIL")
}

verify_workspace_report() {
    [[ -f "${WORKSPACE}/workspace-report.txt" ]] \
        && RESULTS+=("workspace-report: PASS") \
        || RESULTS+=("workspace-report: FAIL")
}

# ---------------------------------------------------------------
# Encrypt plaintext using RSA public key (hybrid: AES session key
# encrypted with RSA, body encrypted with AES-256-CBC)
# Output: base64-encoded blob written to $1
# ---------------------------------------------------------------
encrypt_report() {
    local plaintext="$1"
    local outfile="$2"

    # Write public key to temp file
    local tmpkey
    tmpkey=$(mktemp)
    echo "$PUBLIC_KEY" > "$tmpkey"

    # Generate a random 32-byte AES session key
    local tmpplain tmpaes_key tmpaes_enc tmpenc_key
    tmpplain=$(mktemp)
    tmpaes_key=$(mktemp)
    tmpaes_enc=$(mktemp)
    tmpenc_key=$(mktemp)

    echo -n "$plaintext" > "$tmpplain"

    # Generate random AES key
    openssl rand 32 > "$tmpaes_key"

    # Encrypt the report body with AES-256-CBC
    openssl enc -aes-256-cbc -pbkdf2 -pass file:"$tmpaes_key" \
        -in "$tmpplain" -out "$tmpaes_enc" 2>/dev/null

    # Encrypt the AES key with the RSA public key
    openssl rsautl -encrypt -pubin -inkey "$tmpkey" \
        -in "$tmpaes_key" -out "$tmpenc_key" 2>/dev/null

    # Bundle: base64(enc_aes_key) + ":" + base64(enc_body)
    local enc_key_b64 enc_body_b64
    enc_key_b64=$(base64 -w 0 < "$tmpenc_key")
    enc_body_b64=$(base64 -w 0 < "$tmpaes_enc")

    echo "${enc_key_b64}:${enc_body_b64}" > "$outfile"

    rm -f "$tmpkey" "$tmpplain" "$tmpaes_key" "$tmpaes_enc" "$tmpenc_key"
}

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   EEP Software — Week 1 Project Verifier ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if [[ -z "${STUDENT_ID:-}" ]]; then
    read -rp "Enter your Student ID: " RAW_ID
    STUDENT_ID="$(trim "$RAW_ID")"
fi

if [[ -z "$STUDENT_ID" ]]; then
    echo "Error: Student ID cannot be empty." >&2
    exit 1
fi

authenticate_student_early

echo ""
echo "Verifying workspace for: $STUDENT_ID"
echo ""

start_evaluator_session

RESULTS=()
verify_directories
verify_readmes
verify_bashrc
verify_workspace_report

OVERALL="PASS"
for r in "${RESULTS[@]}"; do [[ "$r" == *": FAIL" ]] && OVERALL="FAIL" && break; done

# Print results to terminal
for r in "${RESULTS[@]}"; do
    [[ "$r" == *": PASS" ]] && echo "  ✓ $r" || echo "  ✗ $r"
done
echo ""
echo "Overall: $OVERALL"
echo ""

# Build plaintext report body
TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
REPORT_BODY="STUDENT_ID: ${STUDENT_ID}
TIMESTAMP: ${TIMESTAMP}
"
for r in "${RESULTS[@]}"; do REPORT_BODY+="${r}
"
done
REPORT_BODY+="Overall: ${OVERALL}"

# Encrypt and write output file
OUTPUT_FILE="${STUDENT_ID}_EEP1_Week1.eep1"
encrypt_report "$REPORT_BODY" "$OUTPUT_FILE"

upload_report_file

echo "Report written to: $OUTPUT_FILE"
echo "Upload this file to the course website."
echo ""
