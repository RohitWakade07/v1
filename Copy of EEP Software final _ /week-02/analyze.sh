#!/bin/bash
# analyze.sh — Server Log Analysis Toolkit
# Week 2 EEP Software Assignment
# Analyzes server.log and produces report.txt

LOG="server.log"
REPORT="report.txt"

# Analysis 1: Total request count
echo "=== Total Request Count ===" > "$REPORT"
wc -l < "$LOG" >> "$REPORT"
echo "" >> "$REPORT"

# Analysis 2: Top 5 IP addresses by request count
echo "=== Top 5 IP Addresses ===" >> "$REPORT"
awk '{print $1}' "$LOG" | sort | uniq -c | sort -rn | head -5 >> "$REPORT"
echo "" >> "$REPORT"

# Analysis 3: Top 5 most requested URLs
echo "=== Top 5 URLs ===" >> "$REPORT"
awk '{print $7}' "$LOG" | sort | uniq -c | sort -rn | head -5 >> "$REPORT"
echo "" >> "$REPORT"

# Analysis 4: HTTP status code distribution
echo "=== Status Code Distribution ===" >> "$REPORT"
awk '{print $9}' "$LOG" | sort | uniq -c | sort -rn >> "$REPORT"
echo "" >> "$REPORT"

echo "Report generated: $REPORT"
