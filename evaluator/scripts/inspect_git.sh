#!/bin/bash
# ==============================================================================
# inspect_git.sh - Git Repository Inspection for Linux Targets
# Outputs structured machine-readable JSON contracts to stdout.
# ==============================================================================

COMMAND=$1
PATH_TARGET=$2

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

# Ensure git is installed
if ! command -v git >/dev/null 2>&1; then
  print_json "error" "false" "Git command-line utility is not installed."
  exit 1
fi

# 1. Validate repository existence
if [ "$COMMAND" = "validate_repo" ]; then
  if git -C "$PATH_TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    print_json "success" "true" "Valid Git repository." "\"target\":\"$PATH_TARGET\""
    exit 0
  else
    print_json "success" "false" "Not a valid Git repository directory." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

# 2. Check current active branch
elif [ "$COMMAND" = "check_branch" ]; then
  EXPECTED_BRANCH=$3
  if git -C "$PATH_TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    ACTUAL_BRANCH=$(git -C "$PATH_TARGET" rev-parse --abbrev-ref HEAD)
    if [ "$ACTUAL_BRANCH" = "$EXPECTED_BRANCH" ]; then
      print_json "success" "true" "Git branch matches expected." "\"target\":\"$PATH_TARGET\",\"expected\":\"$EXPECTED_BRANCH\",\"actual\":\"$ACTUAL_BRANCH\""
      exit 0
    else
      print_json "success" "false" "Git branch mismatch." "\"target\":\"$PATH_TARGET\",\"expected\":\"$EXPECTED_BRANCH\",\"actual\":\"$ACTUAL_BRANCH\""
      exit 1
    fi
  else
    print_json "success" "false" "Not inside a valid Git repository." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

# 3. Check for specific commit hash presence
elif [ "$COMMAND" = "check_commit" ]; then
  COMMIT_HASH=$3
  if git -C "$PATH_TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if git -C "$PATH_TARGET" cat-file -t "$COMMIT_HASH" >/dev/null 2>&1; then
      print_json "success" "true" "Commit hash exists in history." "\"target\":\"$PATH_TARGET\",\"commit\":\"$COMMIT_HASH\""
      exit 0
    else
      print_json "success" "false" "Commit hash not found in repository history." "\"target\":\"$PATH_TARGET\",\"commit\":\"$COMMIT_HASH\""
      exit 1
    fi
  else
    print_json "success" "false" "Not inside a valid Git repository." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

# 4. Check for uncommitted changes
elif [ "$COMMAND" = "check_uncommitted" ]; then
  if git -C "$PATH_TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    # Check if git diff has output
    if [ -z "$(git -C "$PATH_TARGET" status --porcelain)" ]; then
      print_json "success" "true" "No uncommitted modifications." "\"target\":\"$PATH_TARGET\""
      exit 0
    else
      print_json "success" "false" "Uncommitted modifications detected in repo workspace." "\"target\":\"$PATH_TARGET\""
      exit 1
    fi
  else
    print_json "success" "false" "Not inside a valid Git repository." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

else
  print_json "error" "false" "Unknown git inspection command: $COMMAND."
  exit 1
fi
