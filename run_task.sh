#!/bin/sh
set -e

# 0. Refuse to start on a dirty working tree.
#
# The workflow is: aider leaves its changes uncommitted, you read them in meld,
# and you commit if you approve. That only holds if "dirty" means exactly one
# run's output. Starting on top of an unreviewed run merges two sets of changes
# into one diff with nothing to tell them apart, and the review gate silently
# stops being a gate.
#
# Untracked files count. A leftover server/ from an abandoned run is not
# tracked and is exactly the thing that must block.
if [ -n "$(git status --porcelain)" ]; then
    echo "FATAL: working tree is not clean."
    echo "Review and commit, or discard, before starting a task. Otherwise this"
    echo "run's changes and the previous run's are indistinguishable."
    echo
    git status --short
    exit 3
fi

# 1. Pre-flight dependency check
if ! command -v npm >/dev/null 2>&1; then
    echo "FATAL: Test binary 'npm' not found in PATH."
    echo "It should be system-wide: it is installed by provision/00-base.sh."
    echo "If this box was reloaded, re-provision. If the project needs its own,"
    echo "make a virtualenv for it."
    exit 1
fi

# 2. Pre-create and track target files to restrict scope
for file in client/src/db.js client/tests/db.test.js; do
    mkdir -p "$(dirname "$file")"
    touch "$file"
done
git add client/src/db.js client/tests/db.test.js

# 3. Generate the prompt
cat << 'EOF' > TMP.prompt.txt
# Task: frontend_db (ID: 40)

## Objective
Initialize offline-first IndexedDB schema

## Acceptance Criteria
- Create Events table matching PRD schema
- Create Tunes table with transform_data and annotation_data
- Enforce <1000 record constraint logic

## Execution Rules
Execute the objective to meet all acceptance criteria.
CRITICAL: Do not write a brittle or partial solution. If this task is too broad, output the exact phrase REQUIRE_DECOMPOSITION and stop.
EOF

# 4. Execute the autonomous loop
#
# --no-auto-commits so the changes are left dirty for review. It also turns off
# dirty-commits: aider does `if not auto_commits: dirty_commits = False`, so one
# flag covers both and the next run cannot quietly commit work you have not read.
#
# NOTE ON --watch-files: it is deliberately NOT here, because it would do
# nothing. main.py builds the FileWatcher and attaches it to the coder, but the
# watcher is only started by the interactive loop, and --message-file calls
# coder.run(with_message=...) which runs one exchange and returns before that
# loop is ever reached. Use ./watch_task.sh for that workflow instead.
echo "Executing ai-aider for task 40..."
ai-aider \
  --yes \
  --auto-test \
  --no-auto-commits \
  --test-cmd "npm run test -- client/tests/db.test.js" \
  --message-file TMP.prompt.txt \
  client/src/db.js client/tests/db.test.js

# 5. Independent Post-flight Verification
#
# Independent because it does not care what the model believes. A run has
# already reported "everything appears to be working correctly" about a suite
# that could not import its own dependency; this step is what caught it.
#
# Three outcomes, not two. A missing import is not a failing test: the remedy
# is to install something, not to change the code, and reporting both as
# "failed verification" sends the next attempt at the wrong problem -- which is
# exactly how a model ends up rewriting working code to avoid an absent
# library.
echo "Aider exited. Running external verification audit..."
VERIFY_OUT=$(mktemp)
trap 'rm -f "$VERIFY_OUT"' EXIT

if npm run test -- client/tests/db.test.js >"$VERIFY_OUT" 2>&1; then
    cat "$VERIFY_OUT"
    echo "RESULT: Task passed verification."
    echo "Review the diff, commit it, then: ./next_task.py finish"
    exit 0
fi

cat "$VERIFY_OUT"

# Checked against the output rather than the exit status: the verification
# command is whatever the task named, so its exit codes are not knowable here,
# but a Python import failure always says so in the same words.
if grep -qE "ModuleNotFoundError|No module named" "$VERIFY_OUT"; then
    MISSING=$(grep -oE "No module named '[^']*'" "$VERIFY_OUT" | head -1 | cut -d"'" -f2)
    if [ -n "$MISSING" ]; then
        echo "RESULT: Task BLOCKED - missing dependency: $MISSING"
    else
        echo "RESULT: Task BLOCKED - missing dependency (name not parsed)"
    fi
    echo "The code was NOT verified -- this says nothing about whether it works."
    echo "Install the dependency and re-run. Do not ask the model to work"
    echo "around it: it will rewrite the code to avoid the import and the task"
    echo "will then pass without ever testing what was asked for."
    exit 2
fi

echo "RESULT: Task failed verification."
exit 1
