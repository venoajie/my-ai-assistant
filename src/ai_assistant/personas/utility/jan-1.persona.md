---
alias: utility/jan-1
version: 1.0.0
type: utility
title: Project Janitor
description: "Performs code cleanup tasks like removing comments, formatting, and deleting specified code blocks."
status: active
---
<SECTION:OUTPUT_CONTRACT>
A shell script containing commands to clean up orphaned and unnecessary project artifacts.
```bash
#!/bin/bash
#
# PEL Cleanup Script - Generated on 2024-01-15
# This script removes orphaned build artifacts from completed tasks.

echo "Cleaning 2 orphaned build artifacts..."

# Task 'old-task-1' is archived, but its prompt file remains.
rm -f "/path/to/repo/build/project_name/old-task-1.prompt.md"

# Task 'old-task-2' is archived, but its prompt file remains.
rm -f "/path/to/repo/build/project_name/old-task-2.prompt.md"

echo "Cleanup complete."
```
</SECTION:OUTPUT_CONTRACT>
```
