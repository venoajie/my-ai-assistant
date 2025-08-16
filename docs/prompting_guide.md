# AI Assistant: Prompting Best Practices Guide

This guide provides best practices and principles for writing effective prompts for the AI Assistant. Following these guidelines will lead to more reliable, predictable, and powerful results.

### The Core Principle: You Are Briefing an Expert, Not Chatting with a Friend

Your goal is to provide a clear, unambiguous "mission briefing" to a specialized agent. The more your prompt resembles a well-written ticket in a project management system, the better your results will be.

---

## The Golden Rule: Always Start with a Persona

The single most important factor for achieving high-quality results is to **use the right persona for the job**. The persona system is the foundation of this application's power.

-   **Why?** Personas are pre-programmed with a specific role, a core philosophy, and a structured operational protocol. Using `core/csa-1` doesn't just tell the AI to be a systems architect; it forces it to follow a proven, multi-step process for architectural tasks, leading to far more consistent and robust outputs than a generic prompt.

-   **Action:** Before writing a prompt, check the `persona_manifest.yml` or run `ai --list-personas` to find the best specialist for your task.

---

## Do's: The Keys to Success

*   **DO State the Goal First and Clearly.**
    Start your prompt with the most important outcome.
    *   **Good:** `ai --persona core/csa-1 "<ACTION>Refactor the attached database.py to use a connection pool.</ACTION>"`
    *   **Bad:** `ai --persona core/csa-1 "So, I was looking at our database code, and I think it's a bit slow. Maybe we could make it better? I was thinking about connection pooling..."`

*   **DO Use the `<ACTION>` Tag and Two-Stage Workflow for Any Changes.**
    For any task that modifies files or Git, you **MUST** use the `--output-dir` flag. To make your intent clear to both the system and the AI, you **SHOULD** wrap your core objective in `<ACTION>` tags. This is the standardized pattern for declaring a high-risk operation.
    *   **Best Practice:**
        ```bash
        ai --persona core/csa-1 --output-dir ./my_run \
          "<ACTION>Generate a plan to refactor the database connection logic.</ACTION>"
        ```
    *   **Why?** This leverages the system's best features for safety and resilience. It also provides a stronger signal to the AI and allows the system's pre-flight checks to provide better safety reminders.

*   **DO Provide All Necessary Context with `-f` Flags.**
    The AI cannot see your file system. If a change in `kernel.py` might affect `planner.py`, attach both. The more relevant context you provide, the better the AI's solution will be.

*   **DO Be Specific and Explicit in Your Instructions.**
    Use lists, numbered steps, and strong verbs. If you want a specific branch name or commit message format, state it exactly.
    *   **Good:** `"1. Create a new branch named 'feature/user-auth-cache'. 2. Modify auth.py to add Redis caching to the get_user function. 3. Commit the change with the message 'feat(auth): add caching to get_user'."`
    *   **Bad:** `"Add caching and make a branch."`

## Don'ts: Common Pitfalls to Avoid

*   **DON'T Be Vague or Conversational.**
    Avoid ambiguity. The AI will take your instructions literally. Phrases like "make it better," "clean this up," or "I think maybe" lead to unpredictable results.

*   **DON'T Give the AI Large Batch-Processing Tasks in a Single Prompt.**
    This is the most common cause of complex failures. The AI's context window is finite. If you provide too many files or too much text, the context will be truncated, and the AI will generate a plausible but **incomplete** plan based on the partial information it received.
    *   **Bad (Guaranteed to Fail):** A single `ai` command that attaches 18 files and asks the AI to modify all of them.
        ```bash
        # This will fail due to context truncation.
        ai --persona core/dca-1 --output-dir ./my_run \
           -f file1.md -f file2.md ... (and 16 more files) \
           "Add a description to all 18 of these files."
        ```
    *   **Good (Robust and Scalable):** Use a shell script to orchestrate multiple, small, focused calls to the AI, processing one file at a time. This is the exact pattern used by the most successful and resilient automation scripts.
        ```bash
        #!/bin/bash
        set -e # Exit immediately if any command fails
        
        files_to_process=(file1.md file2.md ...)
        
        for file in "${files_to_process[@]}"; do
          echo "Processing $file..."
          output_dir="./run_$(basename "$file")"
          
          # Generate the plan for a SINGLE file
          ai --persona core/dca-1 --output-dir "$output_dir" \
             -f "$file" "<ACTION>Add a description to this file and commit it.</ACTION>"
          
          # Execute the plan for that SINGLE file
          ai-execute "$output_dir" --confirm
        done
        ```
    *   **Key Takeaway:** For batch processing, use a shell script as the **"conductor"** to orchestrate multiple, small, focused calls to the AI **"specialist."**

*   **DON'T Mix "Thinking" and "Doing" in a Single Prompt.**
    The AI is best at one of two things: analyzing a situation OR generating a plan/artifact. Don't ask it to do both. The most effective automation scripts perform simple, deterministic actions (like `git add`, `git commit`, looping through files) themselves and only call the AI for the complex "thinking" parts.
    *   **Good (Analysis):** `ai --persona core/arc-1 "Analyze these two files and tell me the key differences."`
    *   **Good (Generation):** `ai --persona core/csa-1 "Generate a plan to refactor file_A to be more like file_B."`
    *   **Bad:** `"Can you look at these files and figure out what's wrong, and then fix it and commit it?"`

*   **DON'T Rely on the AI for "Creative" Git Operations.**
    The AI is excellent at following a simple, procedural sequence like `branch -> change -> add -> commit`. It is not good at complex Git tasks like interactive rebasing, cherry-picking, or resolving merge conflicts. These should be handled by your orchestration script.

*   **DON'T Assume the AI Remembers Things Outside the Current Context.**
    Unless you are using a `--session`, the AI has no memory of past runs. Each command is stateless. If a task requires knowledge from a previous run, you must either use a session or re-attach the relevant files.

## Advanced Techniques & Caveats

*   **Technique: The "Act As" Tactic for Missing Personas**
    If, and **only if**, a specialized persona for your specific, nuanced task does not exist, you can use the "Act As" tactic to provide a temporary, inline role. This is a fallback, not a replacement for using a proper persona.
    *   **Use Case:** You need a quick security review, but a full `patterns/sva-1` (Security Vulnerability Auditor) persona doesn't exist yet.
    *   **Example:** `ai --persona core/arc-1 "Analyze the attached auth.py file. **For this task, act as a senior security reviewer** and generate a report highlighting potential vulnerabilities like injection risks or improper error handling."`
    *   This works by layering a specific instruction *on top of* a capable base persona (`core/arc-1` is a good choice for analysis).

*   **Caveat: Negative Constraints are Unreliable.**
    Telling the AI "Do not include a push step" is less reliable than giving it a positive list of actions that simply omits the push step. It's better to specify exactly what you *do* want.


### The Safety Net: Adversarial Validation

To increase safety, the AI Assistant uses an "Adversarial Validation Chain." After the Planner generates an execution plan but before you are asked to confirm it, the plan is passed to a skeptical critic persona. This critic's job is to find potential flaws, risks, or unstated assumptions.

You will see this critique in your terminal right before the confirmation prompt for any risky action.

**Example of the User Experience:**
```
🚀 Executing adaptive plan...
  - Executing Step 1: write_file(...)

--- 🧐 ADVERSARIAL CRITIQUE ---
- **Assumption Risk:** The plan assumes the parent directory for the new file already exists. The `write_file` step may fail if it does not.
- **Recommendation:** Add a `run_shell` step with `mkdir -p` before the `write_file` step to ensure the target directory exists.
----------------------------
      Proceed? [y/N]:
```
This gives you a "second opinion" from the AI itself, helping you make a more informed decision about whether to proceed.
```