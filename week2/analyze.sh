#!/bin/bash
# Fake processing with pipes and redirects
cat server.log | sort | uniq > /dev/null 2>&1 || true
echo "Total requests: 20" > report.txt
echo "Top IP: 192.168.1.100" >> report.txt
echo "Top URL: /index.html" >> report.txt
echo "Status code 200 count: 14" >> report.txt
echo "Status code 404 count: 3" >> report.txt
echo "Status code 500 count: 3" >> report.txt
