# ai_assistant/_security_guards.py

"""
This module contains critical, non-configurable security constants for the AI Assistant.

DO NOT MODIFY THE LISTS IN THIS FILE UNLESS YOU ARE A SECURITY EXPERT AND
FULLY UNDERSTAND THE IMPLICATIONS. REMOVING A PATTERN FROM THIS LIST COULD
DIRECTLY LEAD TO CATASTROPHIC DATA LOSS OR SYSTEM COMPROMISE.
"""

# This is an immutable tuple to prevent runtime modification.
# It contains regex patterns for shell commands that must be blocked under all circumstances.
SHELL_COMMAND_BLOCKLIST = (
    r'\brm\s+-rf\s+/(?:\*|\s*$)',
    r'\bformat\b',
    r'\bdel\s+/[sq]',
    r'>\s*/dev/sd[a-z]',
    r'\bdd\s+if=',
    r'\bsudo\s+rm',
    r':\(\)\{.*\}:',
    r'\bchmod\s+777',
    r'\bcurl.*\|\s*sh',
    r'\bwget.*\|\s*sh',
    r'\bwget\s+.*-O\s+/',
    r'\bchown\b|\bchgrp\b',
    r'\bmv\s+.*\s+~\/',          # Moving files to home directory (potential overwrite)
    r'\bfind\b.*-delete\b',      # Find command with delete action
    r'\brm\s+.*\*',              # Remove with wildcards (e.g. rm .*)
    r'\bmv\s+.*\s+/dev/null',     # Move to null (silent deletion)
    r'\btruncate\s+-s\s*0',      # Truncate files to zero length
    # Expanded rule to protect common config and source files by matching any character path
    r'>>?\s*.*\.(py|js|cpp|java|rs|go|php|rb|sh|env|cfg|yml|yaml|toml|json|xml|ini|conf)',
)
