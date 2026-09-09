#!/usr/bin/env python3
import csv
import sys
import os

def main():
    try:
        with open('tasks.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            try:
                first_task = next(reader)
            except StopIteration:
                print("No tasks found in tasks.csv")
                sys.exit(1)
    except FileNotFoundError:
        print("tasks.csv not found in the current directory.")
        sys.exit(1)

    target_files = first_task['target_files'].replace(';', ' ')
    criteria = "- " + first_task['acceptance_criteria'].replace('|', '\n- ')
    verify_cmd = first_task['verification_cmd']
    test_binary = verify_cmd.split()[0] if verify_cmd else "echo"

    script_content = f"""#!/bin/sh
set -e

# 1. Pre-flight dependency check
if ! command -v {test_binary} >/dev/null 2>&1; then
    echo "FATAL: Test binary '{test_binary}' not found in PATH."
    echo "Install it in the project virtualenv before running."
    exit 1
fi

# 2. Pre-create and track target files to restrict scope
for file in {target_files}; do
    mkdir -p "$(dirname "$file")"
    touch "$file"
done
git add {target_files}

# 3. Generate the prompt
cat << 'EOF' > TMP.prompt.txt
# Task: {first_task['title']} (ID: {first_task['id']})

## Objective
{first_task['objective']}

## Acceptance Criteria
{criteria}

## Execution Rules
Execute the objective to meet all acceptance criteria.
CRITICAL: Do not write a brittle or partial solution. If this task is too broad, output the exact phrase REQUIRE_DECOMPOSITION and stop.
EOF

# 4. Execute the autonomous loop
echo "Executing ai-aider for task {first_task['id']}..."
ai-aider \\
  --yes \\
  --auto-test \\
  --test-cmd "{verify_cmd}" \\
  --message-file TMP.prompt.txt \\
  {target_files}

# 5. Independent Post-flight Verification
echo "Aider exited. Running external verification audit..."
if {verify_cmd}; then
    echo "RESULT: Task passed verification."
    exit 0
else
    echo "RESULT: Task failed verification."
    exit 1
fi
"""

    with open('run_task.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)

    os.chmod('run_task.sh', 0o755)
    
    # Ensure TMP.prompt.txt is ignored to prevent repo litter
    if not os.path.exists('.gitignore') or 'TMP.prompt.txt' not in open('.gitignore').read():
        with open('.gitignore', 'a') as f:
            f.write('\nTMP.prompt.txt\n')

    print(f"Generated executable 'run_task.sh' for task {first_task['id']}")

if __name__ == '__main__':
    main()