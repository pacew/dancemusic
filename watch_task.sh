#!/bin/sh
# Interactive watch session for task 35: frontend_scaffold
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
  package.json vitest.config.js client/tests/scaffold.test.js
