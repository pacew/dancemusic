#!/usr/bin/env python3
"""Pick the next task, prepare its runner scripts, and mark it done.

    next_task.py            list tasks whose dependencies are all done
    next_task.py 20         prepare run_task.sh, watch_task.sh and CURRENT-TASK
    next_task.py finish     mark the task named in CURRENT-TASK done, then list

State lives in tasks.csv, in a `done` column holding "" or "y". The CSV is the
interchange format with other models running in web chat interfaces, so it is
edited as conservatively as possible: rows are rewritten as raw text with the
last field replaced, not re-serialised, because Python's csv writer would strip
the quotes around `objective` and `acceptance_criteria` and churn all thirteen
rows the first time anything was marked done.
"""
import csv
import os
import subprocess
import sys

TASKS = 'tasks.csv'
CURRENT = 'CURRENT-TASK'
DONE = 'done'


# --------------------------------------------------------------------- tasks

def read_tasks():
    """Return (header, rows, lines).

    rows is a list of (line_index, dict). line_index points into lines, so a
    row can be rewritten in place without touching any other row.

    Refuses to guess when a record spans multiple lines: the in-place rewrite
    below assumes one line per record, and quietly being wrong about that would
    corrupt the task list.
    """
    if not os.path.exists(TASKS):
        die(f"{TASKS} not found in the current directory.")
    with open(TASKS, newline='', encoding='utf-8') as f:
        lines = f.read().splitlines()
    if not lines:
        die(f"{TASKS} is empty.")

    header = next(csv.reader([lines[0]]))
    rows = []
    for i, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue
        fields = next(csv.reader([line]))
        if len(fields) != len(header):
            die(f"{TASKS} line {i + 1} has {len(fields)} fields, header has "
                f"{len(header)}.\n"
                "     Most likely a quoted field contains a newline. This "
                "script rewrites\n"
                "     rows in place and cannot do that safely, so it stops "
                "rather than\n"
                "     guessing. Put each record on one line.")
        rows.append((i, dict(zip(header, fields))))
    if not rows:
        die(f"{TASKS} has a header but no tasks.")
    return header, rows, lines


def ensure_done_column(header, rows, lines):
    """Add `done` as the rightmost column if it is missing. Returns True if the
    file was changed."""
    if DONE in header:
        return False
    lines[0] = lines[0] + ',' + DONE
    for i, row in rows:
        lines[i] = lines[i] + ','
        row[DONE] = ''
    header.append(DONE)
    return True


def set_done(rows, lines, task_id):
    """Mark one row done by replacing the last field of its raw line.

    Safe as a text operation because `done` is the rightmost column and its
    only values are "" and "y", neither of which needs quoting.
    """
    for i, row in rows:
        if row['id'] == task_id:
            prefix = lines[i].rsplit(',', 1)[0]
            lines[i] = prefix + ',y'
            row[DONE] = 'y'
            return True
    return False


def write_tasks(lines):
    with open(TASKS, 'w', newline='', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def deps_of(row):
    return [d for d in row.get('depends_on', '').split(';') if d.strip()]


def is_done(row):
    return row.get(DONE, '').strip().lower() == 'y'


def available(rows):
    """Tasks not yet done whose dependencies are all done.

    A finished task also has no un-done dependencies, but listing it would make
    the table answer "what exists" rather than "what can I start", which is the
    only question it is asked.
    """
    done_ids = {r['id'] for _, r in rows if is_done(r)}
    return [r for _, r in rows
            if not is_done(r) and all(d in done_ids for d in deps_of(r))]


def blocked_by(rows, row):
    done_ids = {r['id'] for _, r in rows if is_done(r)}
    return [d for d in deps_of(row) if d not in done_ids]


def print_table(rows):
    done = [r for _, r in rows if is_done(r)]
    ready = available(rows)
    print(f"\n{len(done)}/{len(rows)} tasks done.")
    if not ready:
        remaining = [r for _, r in rows if not is_done(r)]
        if not remaining:
            print("All tasks are done.")
        else:
            # Every remaining task waits on something, which for a DAG means a
            # dependency naming a task id that does not exist.
            print("\nNothing is available, and tasks remain. Blocked on:")
            for r in remaining:
                print(f"  {r['id']:>4}  {r['title']:<24} waits on "
                      f"{','.join(blocked_by(rows, r))}")
        return
    print("\nAvailable now:\n")
    print(f"  {'ID':>4}  TITLE")
    for r in ready:
        print(f"  {r['id']:>4}  {r['title']}")
    print(f"\n  next_task.py {ready[0]['id']}\n")


# ------------------------------------------------------------------ git state

def git_dirty():
    """Porcelain output, or None if this is not a git repository."""
    try:
        out = subprocess.run(['git', 'status', '--porcelain'],
                             capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip()


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# -------------------------------------------------------------- script output

def prepare(row):
    target_files = row['target_files'].replace(';', ' ')
    # tasks.csv separates criteria with ";", the same as target_files. An
    # earlier version split on "|", which appears nowhere in the file, so every
    # prompt got all criteria as one run-on bullet.
    criteria = "- " + row['acceptance_criteria'].replace(';', '\n- ')
    verify_cmd = row['verification_cmd']
    test_binary = verify_cmd.split()[0] if verify_cmd else "echo"

    script_content = f"""#!/bin/sh
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
if ! command -v {test_binary} >/dev/null 2>&1; then
    echo "FATAL: Test binary '{test_binary}' not found in PATH."
    echo "It should be system-wide: it is installed by provision/00-base.sh."
    echo "If this box was reloaded, re-provision. If the project needs its own,"
    echo "make a virtualenv for it."
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
# Task: {row['title']} (ID: {row['id']})

## Objective
{row['objective']}

## Acceptance Criteria
{criteria}

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
echo "Executing ai-aider for task {row['id']}..."
ai-aider \\
  --yes \\
  --auto-test \\
  --no-auto-commits \\
  --test-cmd "{verify_cmd}" \\
  --message-file TMP.prompt.txt \\
  {target_files}

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

# Through sh -c, because verification_cmd may be a compound command. With a
# bare `if a && b >FILE`, the redirection binds only to b, so the first half's
# output -- including any npm install failure -- escapes to the terminal and is
# invisible to the BLOCKED check below.
if sh -c "{verify_cmd}" >"$VERIFY_OUT" 2>&1; then
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
"""

    # The watch workflow, which cannot live in run_task.sh -- see the note
    # there. This blocks: aider sits watching the tree, and acts when you save a
    # comment ending in AI! (do it) or AI? (answer it). Written for reviewing in
    # meld and marking up the code in place rather than describing a location in
    # prose.
    watch_content = f"""#!/bin/sh
# Interactive watch session for task {row['id']}: {row['title']}
#
# Leave this running. In any watched file, write a comment ending in AI! and
# save:
#
#     def init_db():   # take the db path as an argument AI!
#
# AI? asks a question instead of making a change. Ctrl-C to stop.
#
# No --auto-test here: in an interactive session it fires after every edit. Use
# /test when you want it.
exec ai-aider \\
  --no-auto-commits \\
  --watch-files \\
  {target_files}
"""

    for name, content in (('run_task.sh', script_content),
                          ('watch_task.sh', watch_content)):
        with open(name, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(name, 0o755)

    # Committed alongside the scripts, so the repository records which task a
    # commit belongs to. `finish` reads the id back out of it.
    with open(CURRENT, 'w', encoding='utf-8') as f:
        f.write(f"{row['id']} {row['title']}\n")

    # Keep generated litter out of the working tree, because run_task.sh
    # refuses to start when the tree is dirty -- and __pycache__ appears the
    # moment anything imports the code, which would block every run after the
    # first for a reason that has nothing to do with the task.
    # node_modules/ matters as much as the others now: run_task.sh refuses to
    # start on a dirty tree, and an npm install drops tens of thousands of
    # untracked files that would block every task from here on.
    ignore_patterns = ['TMP.prompt.txt', '__pycache__/', '*.pyc',
                       'node_modules/']
    existing = ''
    if os.path.exists('.gitignore'):
        with open('.gitignore', encoding='utf-8') as f:
            existing = f.read()
    missing = [p for p in ignore_patterns if p not in existing.split()]
    if missing:
        with open('.gitignore', 'a', encoding='utf-8') as f:
            f.write('\n' + '\n'.join(missing) + '\n')

    print(f"Task {row['id']}: {row['title']}")
    print(f"  targets   {target_files}")
    print(f"  verify    {verify_cmd}")
    print(f"  wrote     run_task.sh, watch_task.sh, {CURRENT}")
    print("\nCommit these, then ./run_task.sh")


def read_current():
    if not os.path.exists(CURRENT):
        die(f"no {CURRENT}. Start a task first: next_task.py <id>")
    with open(CURRENT, encoding='utf-8') as f:
        text = f.read().strip()
    if not text:
        die(f"{CURRENT} is empty.")
    return text.split(None, 1)[0]


# --------------------------------------------------------------------- verbs

def cmd_list(header, rows, lines, changed):
    if changed:
        write_tasks(lines)
        print(f"added a '{DONE}' column to {TASKS}")
    print_table(rows)


def cmd_start(header, rows, lines, changed, task_id):
    match = [r for _, r in rows if r['id'] == task_id]
    if not match:
        die(f"no task with id {task_id}. Run with no arguments to see the list.")
    row = match[0]

    waiting = blocked_by(rows, row)
    if waiting:
        die(f"task {task_id} depends on {','.join(waiting)}, which "
            f"{'is' if len(waiting) == 1 else 'are'} not done.\n"
            "     Run with no arguments to see what is available.")
    if is_done(row):
        print(f"note: task {task_id} is already marked done; preparing it again.")

    if changed:
        write_tasks(lines)
    prepare(row)


def cmd_finish(header, rows, lines, changed):
    dirty = git_dirty()
    if dirty is None:
        die("not a git repository, so 'finish' cannot check that your work is "
            "committed.")
    if dirty:
        print("error: working tree is not clean. Commit or discard first --",
              file=sys.stderr)
        print("       marking a task done is a claim that its work is in the "
              "repository.\n", file=sys.stderr)
        print(dirty, file=sys.stderr)
        sys.exit(1)

    task_id = read_current()
    match = [r for _, r in rows if r['id'] == task_id]
    if not match:
        die(f"{CURRENT} names task {task_id}, which is not in {TASKS}.")
    if is_done(match[0]):
        die(f"task {task_id} is already marked done. Nothing to do.")

    ensure = changed
    if not set_done(rows, lines, task_id):
        die(f"could not find task {task_id} to mark done.")
    write_tasks(lines)
    print(f"task {task_id} ({match[0]['title']}) marked done in {TASKS}"
          + (f" (and a '{DONE}' column was added)" if ensure else ""))
    print(f"commit {TASKS} to record it.")
    print_table(rows)


def main():
    header, rows, lines = read_tasks()
    changed = ensure_done_column(header, rows, lines)

    args = sys.argv[1:]
    if not args:
        cmd_list(header, rows, lines, changed)
    elif args[0] == 'finish':
        cmd_finish(header, rows, lines, changed)
    elif args[0].isdigit():
        cmd_start(header, rows, lines, changed, args[0])
    else:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
