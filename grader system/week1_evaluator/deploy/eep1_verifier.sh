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
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsILIw0+S8v0dAZwsZqC1
pwkLh32OJeAPgV4rzJZDEt5EvepfvfcbIzt721jE101KEtYwbSHtFM+1/puKyO1/
zE9ds4wV7LBPC7I+Y48b22YHsi6EYz4woPCT9A0mAQKAxQjL7TyQBRTELcBJvZ40
b2I9TJZZapzUU6Mk0V0/+InMwe61VVtJKqSUIvyyvBu7xm2uGXUVHLE4hHu926OP
FSbFIMDjCPUuPzavsvQfUiiINSl776GwfPx7FaOZxjvr6u4WGjK/KATRKk0pPEuD
OGLvkZpmEJg3Jqol/DlusLqcYfGQ60FNXqK2Ad6pebExD+Lm24RQ6DAIac8oYPCL
hwIDAQAB
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

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
trim() { echo "$1" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }

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

read -rp "Enter your Student ID: " RAW_ID
STUDENT_ID="$(trim "$RAW_ID")"

if [[ -z "$STUDENT_ID" ]]; then
    echo "Error: Student ID cannot be empty." >&2
    exit 1
fi

echo ""
echo "Verifying workspace for: $STUDENT_ID"
echo ""

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

echo "Report written to: $OUTPUT_FILE"
echo "Upload this file to the course website."
echo ""
