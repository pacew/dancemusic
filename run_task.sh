#!/bin/sh
set -e

# 1. Pre-flight dependency check
if ! command -v pytest >/dev/null 2>&1; then
    echo "FATAL: Test binary 'pytest' not found in PATH."
    echo "Install it in the project virtualenv before running."
    exit 1
fi

# 2. Pre-create and track target files to restrict scope
for file in server/db.py server/tests/test_db.py; do
    mkdir -p "$(dirname "$file")"
    touch "$file"
done
git add server/db.py server/tests/test_db.py

# 3. Generate the prompt
cat << 'EOF' > TMP.prompt.txt
# Task: backend_schema (ID: 010)

## Objective
Initialize SQLite schema for Events and Tunes

## Acceptance Criteria
- Event schema uses UUID for setlists 1:1;Tune schema implements CAS SHA-256 media_hash;Both tables implement updated_at and deleted_at tombstones

## Execution Rules
Execute the objective to meet all acceptance criteria.
CRITICAL: Do not write a brittle or partial solution. If this task is too broad, output the exact phrase REQUIRE_DECOMPOSITION and stop.
EOF

# 4. Execute the autonomous loop
echo "Executing ai-aider for task 010..."
ai-aider \
  --yes \
  --auto-test \
  --test-cmd "pytest server/tests/test_db.py" \
  --message-file TMP.prompt.txt \
  server/db.py server/tests/test_db.py

# 5. Independent Post-flight Verification
echo "Aider exited. Running external verification audit..."
if pytest server/tests/test_db.py; then
    echo "RESULT: Task passed verification."
    exit 0
else
    echo "RESULT: Task failed verification."
    exit 1
fi
