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

# 1. Pre-flight dependency check
if ! command -v pytest >/dev/null 2>&1; then
    echo "FATAL: Test binary 'pytest' not found in PATH."
    echo "It should be system-wide: it is installed by provision/00-base.sh."
    echo "If this box was reloaded, re-provision. If the project needs its own,"
    echo "make a virtualenv for it."
    exit 1
fi

# 2. Pre-create and track target files to restrict scope
for file in server/sync.py server/tests/test_sync.py; do
    mkdir -p "$(dirname "$file")"
    touch "$file"
done
git add server/sync.py server/tests/test_sync.py

# 3. Generate the prompt
cat << 'EOF' > TMP.prompt.txt
# Task: backend_sync (ID: 30)

## Objective
Implement LWW synchronization endpoints

## Acceptance Criteria
- Accept JSON push for Events/Tunes
- Resolve conflicts via unconditional Last-Write-Wins using updated_at
- Process deleted_at tombstones

## Execution Rules
Execute the objective to meet all acceptance criteria.
CRITICAL: Do not write a brittle or partial solution. If this task is too broad, output the exact phrase REQUIRE_DECOMPOSITION and stop.

Do not use flask or another web framework.  Instead use bottle.

# Bottle Framework API Contract

Do not read, import, or modify the file server/bottle.py. It is a large vendored dependency. Use this specification to implement routing and JSON handling.

## Core Imports

from bottle import get, post, request, response, run, HTTPResponse

## Routing and URL Parameters

Use method-specific decorators. Path variables are enclosed in angle brackets.

@get('/sync/events')
def list_events():
return {"events": []}

@post('/sync/events/<event_id>')
def update_event(event_id):
pass

## Reading JSON Payloads

Extract parsed JSON dictionaries using the request.json property.

@post('/sync/tunes')
def sync_tunes():
payload = request.json
if not payload:
return HTTPResponse(status=400, body="Invalid JSON")

```
tune_id = payload.get('id')
return {"status": "merged"}

```

## Returning JSON

Return a standard Python dictionary. Bottle automatically serializes it to a JSON string and sets the Content-Type: application/json header.

@get('/sync/state')
def get_state():
return {
"last_updated": 1700000000,
"status": "synchronized"
}

## Error Handling

Return an HTTPResponse object to set specific status codes for client errors or conflicts.

if conflict_detected:
return HTTPResponse(status=409, body="Conflict detected")

## Initialization

To start the server block, use run().

if **name** == '**main**':
run(host='127.0.0.1', port=8080)

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
echo "Executing ai-aider for task 30..."
ai-aider \
  --yes \
  --auto-test \
  --no-auto-commits \
  --test-cmd "pytest server/tests/test_sync.py" \
  --message-file TMP.prompt.txt \
  server/sync.py server/tests/test_sync.py

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

if pytest server/tests/test_sync.py >"$VERIFY_OUT" 2>&1; then
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
