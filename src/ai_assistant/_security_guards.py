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
    r'\brm\s+-rf\s+/',      # Deleting root filesystem
    r'\bformat\b',          # Formatting drives
    r'\bdel\s+/[sq]',       # Deleting system files on Windows
    r'>\s*/dev/sd[a-z]',    # Overwriting block devices
    r'\bdd\s+if=',          # Low-level disk writing
    r'\bsudo\s+rm',         # Privileged deletion
    r':\(\)\{.*\}:',        # Fork bomb
    r'\bchmod\s+777',       # Overly permissive permissions
    r'\bcurl.*\|\s*sh',     # Pipe to shell from web
    r'\bwget.*\|\s*sh',
    r'\bfind\b.*-delete\b', # Find command with delete action
    r'\brm\s+.*\*',         # Remove with wildcards
    r'\bmv\s+.*\s+/dev/null',# Move to null
    r'\btruncate\s+-s\s*0', # Truncate files
    r'>>?\s*\w+\.(py|js|cpp|java|rs)', # Overwrite or Append to source files
)