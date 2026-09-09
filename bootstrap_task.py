#!/usr/bin/env python3
import csv
import sys

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

    # Format the semicolon-separated lists
    target_files = first_task['target_files'].replace(';', ' ')
    criteria = "- " + first_task['acceptance_criteria'].replace('|', '\n- ')

    # Generate the shell script with a Here-Doc for the prompt
    script_content = f"""#!/bin/sh
# Auto-generated runner for task {first_task['id']}: {first_task['title']}

cat << 'EOF' > TMP.prompt.txt
# Task: {first_task['title']} (ID: {first_task['id']})

## Objective
{first_task['objective']}

## Acceptance Criteria
{criteria}

## Execution Rules
Execute the objective to meet all acceptance criteria. 
CRITICAL: If you determine this task is too broad, complex, or requires structural changes beyond the targeted files, DO NOT attempt a partial or brittle solution. Instead, stop and explicitly state that the task needs to be decomposed by the human or planning model. Requesting decomposition is a successful outcome; writing bad code is not.
EOF

# Execute the aider wrapper
echo "Executing ai-aider for task {first_task['id']}..."
ai-aider \\
  --test-cmd "{first_task['verification_cmd']}" \\
  --message-file TMP.prompt.txt \\
  {target_files}
"""

    with open('run_task.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)

    import os
    os.chmod('run_task.sh', 0o755)
    print(f"Generated executable 'run_task.sh' for task {first_task['id']} ({first_task['title']})")
    print(f"Target files: {target_files}")

if __name__ == '__main__':
    main()