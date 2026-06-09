#!/bin/bash
# EEP2 Week 2 Project Verifier — Server Log Analysis
# Students run this on their machine.
# Checks: analyze.sh exists, is executable, produces report.txt,
# report contains all 4 required analyses.
# Encrypts results with instructor public key.
#
# DO NOT MODIFY THIS SCRIPT.

set -euo pipefail

# ── Instructor's RSA public key ───────────────────────────────────────────────
PUBLIC_KEY='-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApYmNjG2L7Ci4MLlkGmAh
gbzdFNBpaF6dDfcilzfE8n77Y0tPJclieRdlqjBp4mV5nZWJt6HkI/wbGLir7n6E
tx6odtUikrEbkcgYmQ2Ey+MygkxgaEUqJjCow+Sp0tluwnu0Ul/IupUeptDD3xcH
t4oEXadeCozB5W1U4hqlU24VW2O/RIs++ggY78H7fAez/3KFlwL7+Nc2n+RqotEI
xP3k2OH7Ko8YjSS1CdbzOPsQXaCqXwlUN/bxDZca2te6rlogjUw2zkWh8MvH821Z
VBSgsKerVguUmaONJo3UZjqJQ9pBKhOWX84vrKwyHlIXe8JOnIdZTJlk+14xw27Z
bQIDAQAB
-----END PUBLIC KEY-----'

# ── Constants ─────────────────────────────────────────────────────────────────
WORKSPACE="$HOME/eep-software/week-02"
LOGFILE="$WORKSPACE/server.log"
SCRIPT="$WORKSPACE/analyze.sh"
REPORT="$WORKSPACE/report.txt"

API_BASE_URL="${EEP_API_BASE_URL:-http://localhost:5173}"
ASSIGNMENT_SLUG="${EEP_ASSIGNMENT_SLUG:-eep-week2}"
EVALUATOR_KEY="${EEP_EVALUATOR_KEY:-}"
STUDENT_TOKEN="${EEP_STUDENT_TOKEN:-}"
AUTO_UPLOAD="${EEP_AUTO_UPLOAD:-0}"
AUTO_LOGIN="${EEP_AUTO_LOGIN:-0}"
STUDENT_PASSWORD="${EEP_STUDENT_PASSWORD:-}"

# ── Helpers ───────────────────────────────────────────────────────────────────
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

# ── Checks ────────────────────────────────────────────────────────────────────

check_files_exist() {
    [[ -d "$WORKSPACE" ]] && add_check "dir:week-02" "PASS" || add_check "dir:week-02" "FAIL"
    [[ -f "$LOGFILE" ]] && add_check "file:server.log" "PASS" || add_check "file:server.log" "FAIL"
    [[ -f "$SCRIPT" ]] && add_check "file:analyze.sh" "PASS" || add_check "file:analyze.sh" "FAIL"
    [[ -x "$SCRIPT" ]] && add_check "executable:analyze.sh" "PASS" || add_check "executable:analyze.sh" "FAIL"
}

check_script_runs() {
    # Run the script from the workspace directory
    if [[ -f "$SCRIPT" && -x "$SCRIPT" && -f "$LOGFILE" ]]; then
        local tmpdir
        tmpdir=$(mktemp -d)
        cp "$LOGFILE" "$tmpdir/server.log"
        cp "$SCRIPT" "$tmpdir/analyze.sh"
        chmod +x "$tmpdir/analyze.sh"
        if (cd "$tmpdir" && bash analyze.sh >/dev/null 2>&1); then
            add_check "script:runs" "PASS"
            # Check if it produced report.txt
            if [[ -f "$tmpdir/report.txt" ]]; then
                add_check "output:report.txt" "PASS"
                # Copy for analysis
                cp "$tmpdir/report.txt" /tmp/eep2_test_report.txt
            else
                add_check "output:report.txt" "FAIL"
            fi
        else
            add_check "script:runs" "FAIL"
            add_check "output:report.txt" "FAIL"
        fi
        rm -rf "$tmpdir"
    else
        add_check "script:runs" "FAIL"
        add_check "output:report.txt" "FAIL"
    fi
}

check_report_content() {
    local report="/tmp/eep2_test_report.txt"
    if [[ ! -f "$report" ]]; then
        # Use student's existing report.txt if script didn't produce one in test
        if [[ -f "$REPORT" ]]; then
            report="$REPORT"
        else
            add_check "analysis:request_count" "FAIL"
            add_check "analysis:top_ips" "FAIL"
            add_check "analysis:top_urls" "FAIL"
            add_check "analysis:status_codes" "FAIL"
            return
        fi
    fi

    # Check 1: Total request count (should contain "30" or a number)
    if grep -qiE '(total|count|request)' "$report" && grep -qE '[0-9]+' "$report"; then
        add_check "analysis:request_count" "PASS"
    else
        add_check "analysis:request_count" "FAIL"
    fi

    # Check 2: Top IP addresses (should contain IP addresses)
    if grep -qE '([0-9]{1,3}\.){3}[0-9]{1,3}' "$report"; then
        add_check "analysis:top_ips" "PASS"
    else
        add_check "analysis:top_ips" "FAIL"
    fi

    # Check 3: Top URLs (should contain URL paths)
    if grep -qE '/[a-zA-Z]' "$report"; then
        add_check "analysis:top_urls" "PASS"
    else
        add_check "analysis:top_urls" "FAIL"
    fi

    # Check 4: Status code distribution (should contain HTTP status codes)
    if grep -qE '(200|30[0-9]|40[0-9]|50[0-9])' "$report"; then
        add_check "analysis:status_codes" "PASS"
    else
        add_check "analysis:status_codes" "FAIL"
    fi

    rm -f /tmp/eep2_test_report.txt
}

check_pipeline_usage() {
    # Check that analyze.sh uses pipes (|) — single pipeline requirement
    if [[ -f "$SCRIPT" ]]; then
        if grep -q '|' "$SCRIPT"; then
            add_check "technique:pipelines" "PASS"
        else
            add_check "technique:pipelines" "FAIL"
        fi
        # Check uses > or >> for output redirection
        if grep -qE '>>?' "$SCRIPT"; then
            add_check "technique:redirection" "PASS"
        else
            add_check "technique:redirection" "FAIL"
        fi
    else
        add_check "technique:pipelines" "FAIL"
        add_check "technique:redirection" "FAIL"
    fi
}

# ── Encryption ────────────────────────────────────────────────────────────────
encrypt_report() {
    local plaintext="$1"
    local outfile="$2"
    local tmpkey tmplain tmpaes_key tmpaes_enc tmpenc_key
    tmpkey=$(mktemp); tmplain=$(mktemp); tmpaes_key=$(mktemp)
    tmpaes_enc=$(mktemp); tmpenc_key=$(mktemp)

    echo "$PUBLIC_KEY" > "$tmpkey"
    echo -n "$plaintext" > "$tmplain"
    openssl rand 32 > "$tmpaes_key"
    openssl enc -aes-256-cbc -pbkdf2 -pass file:"$tmpaes_key" -in "$tmplain" -out "$tmpaes_enc" 2>/dev/null
    openssl rsautl -encrypt -pubin -inkey "$tmpkey" -in "$tmpaes_key" -out "$tmpenc_key" 2>/dev/null

    local enc_key_b64 enc_body_b64
    enc_key_b64=$(base64 -w 0 < "$tmpenc_key")
    enc_body_b64=$(base64 -w 0 < "$tmpaes_enc")
    echo "${enc_key_b64}:${enc_body_b64}" > "$outfile"

    rm -f "$tmpkey" "$tmplain" "$tmpaes_key" "$tmpaes_enc" "$tmpenc_key"
}

# ── Main ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  EEP Software — Week 2 Project Verifier  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if [[ -z "${STUDENT_ID:-}" ]]; then
    read -rp "Enter your Student ID: " RAW_ID
    STUDENT_ID="$(trim "$RAW_ID")"
fi
[[ -z "$STUDENT_ID" ]] && echo "Error: Student ID cannot be empty." >&2 && exit 1

authenticate_student_early

echo ""
echo "Verifying Week 2 assignment for: $STUDENT_ID"
echo "Workspace: $WORKSPACE"
echo ""

start_evaluator_session

check_files_exist
check_script_runs
check_report_content
check_pipeline_usage

# Overall
OVERALL="PASS"
for r in "${RESULTS[@]}"; do [[ "$r" == *": FAIL" ]] && OVERALL="FAIL" && break; done

# Print results
for r in "${RESULTS[@]}"; do
    [[ "$r" == *": PASS" ]] && echo "  ✓ $r" || echo "  ✗ $r"
done
echo ""
echo "Overall: $OVERALL"
echo ""

# Build and encrypt
TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
REPORT_BODY="STUDENT_ID: ${STUDENT_ID}
TIMESTAMP: ${TIMESTAMP}
WEEK: 2
"
for r in "${RESULTS[@]}"; do REPORT_BODY+="${r}
"; done
REPORT_BODY+="Overall: ${OVERALL}"

OUTPUT_FILE="${STUDENT_ID}_EEP2_Week2.eep2"
encrypt_report "$REPORT_BODY" "$OUTPUT_FILE"

upload_report_file

echo "Report written to: $OUTPUT_FILE"
echo "Upload this file to the course website."
echo ""
