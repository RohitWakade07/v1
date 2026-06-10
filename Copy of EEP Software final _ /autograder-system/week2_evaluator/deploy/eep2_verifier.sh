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
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsILIw0+S8v0dAZwsZqC1
pwkLh32OJeAPgV4rzJZDEt5EvepfvfcbIzt721jE101KEtYwbSHtFM+1/puKyO1/
zE9ds4wV7LBPC7I+Y48b22YHsi6EYz4woPCT9A0mAQKAxQjL7TyQBRTELcBJvZ40
b2I9TJZZapzUU6Mk0V0/+InMwe61VVtJKqSUIvyyvBu7xm2uGXUVHLE4hHu926OP
FSbFIMDjCPUuPzavsvQfUiiINSl776GwfPx7FaOZxjvr6u4WGjK/KATRKk0pPEuD
OGLvkZpmEJg3Jqol/DlusLqcYfGQ60FNXqK2Ad6pebExD+Lm24RQ6DAIac8oYPCL
hwIDAQAB
-----END PUBLIC KEY-----'

# ── Constants ─────────────────────────────────────────────────────────────────
WORKSPACE="$HOME/eep-software/week-02"
LOGFILE="$WORKSPACE/server.log"
SCRIPT="$WORKSPACE/analyze.sh"
REPORT="$WORKSPACE/report.txt"

# ── Helpers ───────────────────────────────────────────────────────────────────
trim() { echo "$1" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }

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

read -rp "Enter your Student ID: " RAW_ID
STUDENT_ID="$(trim "$RAW_ID")"
[[ -z "$STUDENT_ID" ]] && echo "Error: Student ID cannot be empty." >&2 && exit 1

echo ""
echo "Verifying Week 2 assignment for: $STUDENT_ID"
echo "Workspace: $WORKSPACE"
echo ""

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

echo "Report written to: $OUTPUT_FILE"
echo "Upload this file to the course website."
echo ""
