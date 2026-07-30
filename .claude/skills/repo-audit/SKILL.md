---
name: repo-audit
description: Audit this training repo for convention violations (leftover demo_ files, missing EXAM TAKEAWAY lines, junk files). Use when asked to audit or check repo hygiene.
context: fork
allowed-tools: Read, Grep, Glob, Bash(git status:*)
---
# Repo hygiene audit

Steps:
1. Find leftover throwaway files: demo_* anywhere under week*/ folders.
2. Check that every .py file under week*/ ends with a "# EXAM TAKEAWAY:" comment line.
3. Run git status and flag junk that should be ignored (.DS_Store, .venv, caches).

Report back ONLY a short summary: one line per finding, or "All clean" if nothing found.
Do not modify any files.
