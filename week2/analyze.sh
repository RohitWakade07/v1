#!/bin/bash
# Analyzes server.log and writes report.txt

LOG="server.log"
OUT="report.txt"

echo "=== Log Analysis Report ===" > "$OUT"
echo "" >> "$OUT"

# Total requests
TOTAL=$(wc -l < "$LOG")
echo "Total Requests: $TOTAL" >> "$OUT"
echo "" >> "$OUT"

# Top 3 IP addresses
echo "Top IP Addresses:" >> "$OUT"
awk '{print $1}' "$LOG" | sort | uniq -c | sort -rn | head -3 >> "$OUT"
echo "" >> "$OUT"

# Top 3 requested URLs
echo "Top URLs:" >> "$OUT"
awk '{print $7}' "$LOG" | sort | uniq -c | sort -rn | head -3 >> "$OUT"
echo "" >> "$OUT"

# HTTP status code distribution
echo "Status Code Distribution:" >> "$OUT"
awk '{print $9}' "$LOG" | sort | uniq -c | sort -rn >> "$OUT"
