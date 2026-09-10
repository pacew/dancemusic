#!/usr/bin/env python3
"""Pick the next task, prepare its runner scripts, and mark it done.

    next_task.py            list tasks whose dependencies are all done
    next_task.py 20         prepare TMP.run, TMP.interactive, TMP.test and CURRENT-TASK
    next_task.py finish     mark the task named in CURRENT-TASK done, then list

State lives in tasks.csv, in a `done` column holding "" or "y". 
"""
import csv
import os
import subprocess
import sys

TASKS = 'tasks.csv'
CURRENT = 'TMP.CURRENT-TASK'
DONE = 'done'


# --------------------------------------------------------------------- tasks

def read_tasks():
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
                f"{len(header)}.\nPut each record on one line.")
        rows.append((i, dict(zip(header, fields))))
    if not rows:
        die(f"{TASKS} has a header but no tasks.")
    return header, rows, lines


def ensure_done_column(header, rows, lines):
    if DONE in header:
        return False
    lines[0] = lines[0] + ',' + DONE
    for i, row in rows:
        lines[i] = lines[i] + ','
        row[DONE] = ''
    header.append(DONE)
    return True


def set_done(rows, lines, task_id):
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
            print("\nNothing is available, and tasks remain. Blocked on:")
            for r in remaining:
                print(f"  {r['id']:>4}  {r['title']:<24} waits on "
                      f"{','.join(blocked_by(rows, r))}")
        return
    print("\nAvailable now:\n")
    print(f"  {'ID':>4}  TITLE")
    for r in ready:
        print(f"  {r['id']:>4}  {r['title']}")
    print(f"\n  ./next_task.py {ready[0]['id']}\n")


# ------------------------------------------------------------------ git state

def git_dirty():
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
    target_files_list = [f.strip() for f in row['target_files'].split(';') if f.strip()]
    target_files_str = ' '.join(target_files_list)
    criteria = "- " + row['acceptance_criteria'].replace(';', '\n- ')
    verify_cmd = row['verification_cmd']
    test_binary = verify_cmd.split()[0] if verify_cmd else "echo"

    # 1. Pre-create and track target files to restrict scope
    # (Done in python so it happens *after* the dirty check prompt)
    for fpath in target_files_list:
        dname = os.path.dirname(fpath)
        if dname:
            os.makedirs(dname, exist_ok=True)
        if not os.path.exists(fpath):
            open(fpath, 'w').close()
            
    if target_files_list:
        subprocess.run(['git', 'add'] + target_files_list, check=False)

    # 2. Write the Prompt File Directly
    prompt_content = f"""# Task: {row['title']} (ID: {row['id']})

## Objective
{row['objective']}

## Acceptance Criteria
{criteria}

## Execution Rules
Execute the objective to meet all acceptance criteria.
CRITICAL: Do not write a brittle or partial solution. If this task is too broad, output the exact phrase REQUIRE_DECOMPOSITION and stop.
"""
    with open('TMP.prompt', 'w', encoding='utf-8') as f:
        f.write(prompt_content)

    # 3. Create TMP.run
    run_content = f"""#!/bin/bash
set -e

if ! command -v {test_binary} >/dev/null 2>&1; then
    echo "FATAL: Test binary '{test_binary}' not found in PATH."
    exit 1
fi

# Clean history for a pristine headless run
rm -f .aider.chat.history.md

echo "Executing ai-aider for task {row['id']}..."
ai-aider \\
  --yes \\
  --auto-test \\
  --no-auto-commits \\
  --test-cmd "{verify_cmd}" \\
  --message-file TMP.prompt \\
  {target_files_str}

echo "Aider exited. Running external verification audit..."
VERIFY_OUT=$(mktemp)
trap 'rm -f "$VERIFY_OUT"' EXIT

if sh -c "{verify_cmd}" >"$VERIFY_OUT" 2>&1; then
    cat "$VERIFY_OUT"
    echo "RESULT: Task passed verification."
    echo "Review the diff, commit it, then: ./next_task.py finish"
    exit 0
fi

cat "$VERIFY_OUT"
if grep -qE "ModuleNotFoundError|No module named" "$VERIFY_OUT"; then
    echo "RESULT: Task BLOCKED - missing dependency."
    exit 2
fi

echo "RESULT: Task failed verification."
exit 1
"""

    # 4. Create TMP.interactive
    interactive_msg = (
        "This is an interactive session following up on a failed attempt to accomplish "
        "what is specified in TMP.prompt. Any dirty files in the directory are "
        "work-in-progress toward that goal. Please review the current state and "
        "await my instructions."
    )
    
    watch_content = f"""#!/bin/bash
# Interactive watch session for task {row['id']}: {row['title']}

read -p "Fresh session or Preserve chat history (F/p)? " choice
if [[ -z "$choice" || "$choice" =~ ^[Ff] ]]; then
    rm -f .aider.chat.history.md
    echo "Starting fresh session."
else
    echo "Preserving chat history."
fi

exec ai-aider \\
  --no-auto-commits \\
  --watch-files \\
  {target_files_str}
"""

    # 5. Create TMP.test
    test_content = f"""#!/bin/bash
# Manual verification for task {row['id']}: {row['title']}

{verify_cmd}
"""

    for name, content in (('TMP.run', run_content), ('TMP.interactive', watch_content), ('TMP.test', test_content)):
        with open(name, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(name, 0o755)

    with open(CURRENT, 'w', encoding='utf-8') as f:
        f.write(f"{row['id']} {row['title']}\n")

    # 6. Gitignore updates
    ignore_patterns = ['TMP.*', '__pycache__/', '*.pyc', 'node_modules/', 'backend/data/', '.aider*']
    existing = ''
    if os.path.exists('.gitignore'):
        with open('.gitignore', encoding='utf-8') as f:
            existing = f.read()
    missing = [p for p in ignore_patterns if p not in existing.split()]
    if missing:
        with open('.gitignore', 'a', encoding='utf-8') as f:
            f.write('\n' + '\n'.join(missing) + '\n')

    print(f"Task {row['id']}: {row['title']}")
    print(f"  targets   {target_files_str}")
    print(f"  verify    {verify_cmd}")
    print(f"  wrote     TMP.run, TMP.interactive, TMP.test, TMP.prompt, {CURRENT}")
    print("\nNext step: ./TMP.run")


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
            f"{'is' if len(waiting) == 1 else 'are'} not done.")

    dirty = git_dirty()
    if dirty:
        print("WARNING: Working tree is not clean:")
        print(dirty)
        ans = input("\nContinue anyway? (y/n): ").strip().lower()
        if ans != 'y':
            print("Aborted.")
            sys.exit(0)

    if is_done(row):
        print(f"\nWARNING: Task {task_id} is already marked done. Proceeding to set it up anyway.\n", file=sys.stderr)

    if changed:
        write_tasks(lines)
    prepare(row)


def cmd_finish(header, rows, lines, changed):
    dirty = git_dirty()
    if dirty is None:
        die("not a git repository.")
    if dirty:
        print("error: working tree is not clean. Commit or discard first --", file=sys.stderr)
        print("       marking a task done is a claim that its work is in the repository.\n", file=sys.stderr)
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
    print(f"task {task_id} ({match[0]['title']}) marked done in {TASKS}")
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
