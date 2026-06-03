#!/bin/bash
# ==============================================================================
# inspect_process.sh - Process and Port Inspection for Linux Targets
# Outputs structured machine-readable JSON contracts to stdout.
# ==============================================================================

COMMAND=$1
TARGET=$2

print_json() {
  local status=$1
  local passed=$2
  local reason=$3
  local extra_kv=$4
  
  local json="{\"status\":\"$status\",\"passed\":$passed,\"reason\":\"$reason\""
  if [ -n "$extra_kv" ]; then
    json="$json,$extra_kv"
  fi
  json="$json}"
  echo "$json"
}

# 1. Verify process is running
if [ "$COMMAND" = "process_running" ]; then
  if pgrep -f "$TARGET" > /dev/null 2>&1 || ps aux | grep -v grep | grep "$TARGET" > /dev/null 2>&1; then
    print_json "success" "true" "Process is running." "\"process\":\"$TARGET\""
    exit 0
  else
    print_json "success" "false" "Process is not running." "\"process\":\"$TARGET\""
    exit 1
  fi

# 2. Verify port is listening
elif [ "$COMMAND" = "port_listening" ]; then
  PORT=$TARGET
  if command -v ss >/dev/null 2>&1; then
    LISTEN_CHECK=$(ss -tln | grep -E ":$PORT\b" || ss -uln | grep -E ":$PORT\b")
  elif command -v netstat >/dev/null 2>&1; then
    LISTEN_CHECK=$(netstat -tln | grep -E ":$PORT\b" || netstat -uln | grep -E ":$PORT\b")
  else
    # Fallback checking via /proc/net/tcp hex representation or basic curl / nc connection
    LISTEN_CHECK=$(cat /proc/net/tcp 2>/dev/null | grep -i "$(printf ':%04X' "$PORT")")
  fi
  
  if [ -n "$LISTEN_CHECK" ]; then
    print_json "success" "true" "Port $PORT is listening." "\"port\":$PORT"
    exit 0
  else
    print_json "success" "false" "Port $PORT is not active." "\"port\":$PORT"
    exit 1
  fi

else
  print_json "error" "false" "Unknown process inspection command: $COMMAND."
  exit 1
fi
