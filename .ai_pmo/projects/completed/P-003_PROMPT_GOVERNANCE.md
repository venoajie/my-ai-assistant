# Project Charter: P-003 - Prompt Governance Engine

- **version**: 1.0
- **status**: PROPOSED
- **goal**: "Improve system reliability and user education by implementing an enhanced deterministic pre-flight check that validates user prompts against established best practices."

---
## Project Roadmap

### Phase 1: Implement Enhanced Sanity Checker
- **Objective:** Modify the `_run_prompt_sanity_checks` function in `cli.py` to implement the new, pattern-based validation logic.
- **Specialist:** `domains/programming/python-expert-1`
- **Status:** **PENDING**
- **Inputs:** `cli.py`, `governance.yml` (for risky keywords), `tools.py` (for list of workflow tools).
- **Output:** A modified `cli.py` with the new warning system.

### Phase 2: Update Documentation
- **Objective:** Update `prompting_guide.md` to document this new safety feature and explain its benefits.
- **Specialist:** `domains/programming/dca-1`
- **Status:** BLOCKED (depends on Phase 1)
- **Inputs:** The new `cli.py` and examples of its output.
- **Output:** Updated `prompting_guide.md`.



**Example Ambiguous Prompt:**
> `"Execute the current task... Propose changes to the blueprint and system contracts..."`

**Current (Old) System Warning:**
```
[warning] [1] Your prompt seems to request a system modification. For clarity and safety, wrap your goal in <ACTION> tags and use the --output-dir flag.
```
*(This is a generic, low-value warning that is easy to ignore.)*

**Proposed New System Warning:**
```
============================================================
           - PROMPTING BEST PRACTICE ALERT -
============================================================
⚠️  Your prompt requests a file modification but is ambiguous.

- REASON: The prompt contains risky keywords ('changes') but does not specify a high-level workflow tool. This can lead to unpredictable or unsafe plans.

- RECOMMENDATION: For maximum reliability, explicitly constrain the AI by naming the tool and its required arguments.

- EXAMPLE OF A MORE ROBUST PROMPT:
  "Using the execute_refactoring_workflow tool, apply the necessary changes to [file1] and [file2]..."

Proceeding with ambiguous prompt...
------------------------------------------------------------
```