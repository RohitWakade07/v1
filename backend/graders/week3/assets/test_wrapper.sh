#!/bin/bash
bash organize.sh > /dev/null 2>&1
no_args_exit=$?
bash organize.sh /totally_nonexistent_dir_xyz > /dev/null 2>&1
nonexistent_exit=$?
bash organize.sh test_mixed > stdout.txt 2>&1
main_exit=$?
cat <<EOF > result.json
{
  "no_args_exit": $no_args_exit,
  "nonexistent_exit": $nonexistent_exit,
  "main_exit": $main_exit
}
EOF
cat stdout.txt
