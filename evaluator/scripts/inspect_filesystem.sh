#!/bin/bash
# ==============================================================================
# inspect_filesystem.sh - Canonical Filesystem Inspection for Linux Targets
# Outputs structured machine-readable JSON contracts to stdout.
# ==============================================================================

COMMAND=$1
PATH_TARGET=$2

# Helper to print validation JSON outputs
print_json() {
  local status=$1
  local passed=$2
  local reason=$3
  local extra_kv=$4 # Extra comma-separated key-value pairs
  
  local json="{\"status\":\"$status\",\"passed\":$passed,\"reason\":\"$reason\""
  if [ -n "$extra_kv" ]; then
    json="$json,$extra_kv"
  fi
  json="$json}"
  echo "$json"
}

# 1. File existence validation
if [ "$COMMAND" = "file_exists" ]; then
  if [ -f "$PATH_TARGET" ]; then
    print_json "success" "true" "File exists." "\"target\":\"$PATH_TARGET\""
    exit 0
  else
    print_json "success" "false" "File does not exist." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

# 2. Directory existence validation
elif [ "$COMMAND" = "dir_exists" ]; then
  if [ -d "$PATH_TARGET" ]; then
    print_json "success" "true" "Directory exists." "\"target\":\"$PATH_TARGET\""
    exit 0
  else
    print_json "success" "false" "Directory does not exist." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

# 3. File extension validation
elif [ "$COMMAND" = "check_extension" ]; then
  EXPECTED_EXT=$3
  ACTUAL_EXT="${PATH_TARGET##*.}"
  if [ -f "$PATH_TARGET" ] && [ "$ACTUAL_EXT" = "$EXPECTED_EXT" ]; then
    print_json "success" "true" "Extension matches." "\"target\":\"$PATH_TARGET\",\"expected\":\"$EXPECTED_EXT\",\"actual\":\"$ACTUAL_EXT\""
    exit 0
  else
    print_json "success" "false" "Extension mismatch or file not found." "\"target\":\"$PATH_TARGET\",\"expected\":\"$EXPECTED_EXT\""
    exit 1
  fi

# 4. Minimum/maximum size validation
elif [ "$COMMAND" = "check_size" ]; then
  MIN_SIZE=$3
  MAX_SIZE=$4
  if [ -f "$PATH_TARGET" ]; then
    # Cross-platform stat for file size in bytes
    if stat -c %s "$PATH_TARGET" >/dev/null 2>&1; then
      FILE_SIZE=$(stat -c %s "$PATH_TARGET")
    else
      FILE_SIZE=$(wc -c < "$PATH_TARGET" | tr -d ' ')
    fi
    
    PASSED="true"
    REASON="Size checks passed."
    if [ -n "$MIN_SIZE" ] && [ "$FILE_SIZE" -lt "$MIN_SIZE" ]; then
      PASSED="false"
      REASON="File size $FILE_SIZE is less than minimum $MIN_SIZE."
    fi
    if [ -n "$MAX_SIZE" ] && [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
      PASSED="false"
      REASON="File size $FILE_SIZE is greater than maximum $MAX_SIZE."
    fi
    
    print_json "success" "$PASSED" "$REASON" "\"target\":\"$PATH_TARGET\",\"size_bytes\":$FILE_SIZE"
    if [ "$PASSED" = "true" ]; then exit 0; else exit 1; fi
  else
    print_json "success" "false" "File not found for size check." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

# 5. Content pattern validation (grep check)
elif [ "$COMMAND" = "check_content" ]; then
  PATTERN=$3
  if [ -f "$PATH_TARGET" ]; then
    if grep -E "$PATTERN" "$PATH_TARGET" > /dev/null 2>&1; then
      print_json "success" "true" "Pattern found." "\"target\":\"$PATH_TARGET\",\"pattern\":\"$PATTERN\""
      exit 0
    else
      print_json "success" "false" "Pattern not found." "\"target\":\"$PATH_TARGET\",\"pattern\":\"$PATTERN\""
      exit 1
    fi
  else
    print_json "success" "false" "File not found for content check." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

# 6. Permission check (octal permissions stat)
elif [ "$COMMAND" = "check_permission" ]; then
  EXPECTED_PERM=$3
  if [ -e "$PATH_TARGET" ]; then
    # Fetch octal permissions
    if stat -c %a "$PATH_TARGET" >/dev/null 2>&1; then
      ACTUAL_PERM=$(stat -c %a "$PATH_TARGET")
    elif stat -f %Lp "$PATH_TARGET" >/dev/null 2>&1; then # BSD stat
      ACTUAL_PERM=$(stat -f %Lp "$PATH_TARGET")
    else
      # Fallback to general read-only permissions check if stat fails
      ACTUAL_PERM="unknown"
    fi
    
    if [ "$ACTUAL_PERM" = "$EXPECTED_PERM" ]; then
      print_json "success" "true" "Permissions match." "\"target\":\"$PATH_TARGET\",\"expected\":\"$EXPECTED_PERM\",\"actual\":\"$ACTUAL_PERM\""
      exit 0
    else
      print_json "success" "false" "Permissions mismatch." "\"target\":\"$PATH_TARGET\",\"expected\":\"$EXPECTED_PERM\",\"actual\":\"$ACTUAL_PERM\""
      exit 1
    fi
  else
    print_json "success" "false" "Target not found for permission check." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

# 7. Archive structural inspection (zip/tar extraction stats)
elif [ "$COMMAND" = "check_archive" ]; then
  FORMAT=$3
  CONTAINS_FILE=$4
  if [ -f "$PATH_TARGET" ]; then
    PASSED="true"
    REASON="Archive valid."
    
    if [ "$FORMAT" = "zip" ]; then
      if unzip -t "$PATH_TARGET" > /dev/null 2>&1; then
        if [ -n "$CONTAINS_FILE" ] && ! unzip -l "$PATH_TARGET" | grep "$CONTAINS_FILE" > /dev/null 2>&1; then
          PASSED="false"
          REASON="Archive does not contain expected file: $CONTAINS_FILE."
        fi
      else
        PASSED="false"
        REASON="Archive is corrupted or not a valid ZIP file."
      fi
    elif [ "$FORMAT" = "tar" ] || [ "$FORMAT" = "tar.gz" ] || [ "$FORMAT" = "tgz" ]; then
      if tar -tf "$PATH_TARGET" > /dev/null 2>&1; then
        if [ -n "$CONTAINS_FILE" ] && ! tar -tf "$PATH_TARGET" | grep "$CONTAINS_FILE" > /dev/null 2>&1; then
          PASSED="false"
          REASON="Archive does not contain expected file: $CONTAINS_FILE."
        fi
      else
        PASSED="false"
        REASON="Archive is corrupted or not a valid TAR package."
      fi
    else
      PASSED="false"
      REASON="Unsupported archive format: $FORMAT."
    fi
    
    print_json "success" "$PASSED" "$REASON" "\"target\":\"$PATH_TARGET\",\"format\":\"$FORMAT\""
    if [ "$PASSED" = "true" ]; then exit 0; else exit 1; fi
  else
    print_json "success" "false" "Archive file not found." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

# 8. Syntax validation (JSON/YAML)
elif [ "$COMMAND" = "check_json_yaml" ]; then
  FORMAT=$3
  if [ -f "$PATH_TARGET" ]; then
    PASSED="true"
    REASON="Valid syntax."
    
    if [ "$FORMAT" = "json" ]; then
      # Use python json verification to be ultra-compatible
      if python -m json.tool "$PATH_TARGET" >/dev/null 2>&1; then
        PASSED="true"
      else
        PASSED="false"
        REASON="Invalid JSON syntax."
      fi
    elif [ "$FORMAT" = "yaml" ]; then
      # Use python PyYAML verification
      if python -c "import yaml; yaml.safe_load(open('$PATH_TARGET'))" >/dev/null 2>&1; then
        PASSED="true"
      else
        PASSED="false"
        REASON="Invalid YAML syntax."
      fi
    else
      PASSED="false"
      REASON="Unsupported formatting check: $FORMAT."
    fi
    
    print_json "success" "$PASSED" "$REASON" "\"target\":\"$PATH_TARGET\",\"format\":\"$FORMAT\""
    if [ "$PASSED" = "true" ]; then exit 0; else exit 1; fi
  else
    print_json "success" "false" "File not found for syntax verification." "\"target\":\"$PATH_TARGET\""
    exit 1
  fi

else
  print_json "error" "false" "Unknown inspection command: $COMMAND."
  exit 1
fi
