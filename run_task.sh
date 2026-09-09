#!/bin/sh
# Auto-generated runner for task 010: backend_schema

cat << 'EOF' > TMP.prompt.txt
# Task: backend_schema (ID: 010)

## Objective
Initialize SQLite schema for Events and Tunes

## Acceptance Criteria
- Event schema uses UUID for setlists 1:1;Tune schema implements CAS SHA-256 media_hash;Both tables implement updated_at and deleted_at tombstones

## Execution Rules
Execute the objective to meet all acceptance criteria. 
CRITICAL: If you determine this task is too broad, complex, or requires structural changes beyond the targeted files, DO NOT attempt a partial or brittle solution. Instead, stop and explicitly state that the task needs to be decomposed by the human or planning model. Requesting decomposition is a successful outcome; writing bad code is not.
EOF

# Execute the aider wrapper
echo "Executing ai-aider for task 010..."
ai-aider \
  --test-cmd "pytest server/tests/test_db.py" \
  --message-file TMP.prompt.txt \
  server/db.py server/tests/test_db.py
