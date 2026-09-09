#!/bin/sh
# Interactive watch session for task 010: backend_schema
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
exec ai-aider \
  --no-auto-commits \
  --watch-files \
  server/db.py server/tests/test_db.py
