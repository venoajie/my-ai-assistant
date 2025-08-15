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
    *   **Good:** `ai --persona core/csa-1 "Refactor the attached database.py to use a connection pool."`
    *   **Bad:** `ai --persona core/csa-1 "So, I was looking at our database code, and I think it's a bit slow. Maybe we could make it better? I was thinking about connection pooling..."`

*   **DO Use the Two-Stage Workflow for Any Changes.**
    For any task that modifies files or Git, always use the `--output-dir` flag and the "generate a plan" phrasing. This leverages the system's best feature for safety and resilience.
    *   **Good:** `"Generate a complete execution plan to be saved in a manifest file. The plan must..."`
    *   **Bad:** `"Fix the bug in this file and commit it."`

*   **DO Provide All Necessary Context with `-f` Flags.**
    The AI cannot see your file system. If a change in `kernel.py` might affect `planner.py`, attach both. The more relevant context you provide, the better the AI's solution will be.

*   **DO Be Specific and Explicit in Your Instructions.**
    Use lists, numbered steps, and strong verbs. If you want a specific branch name or commit message format, state it exactly.
    *   **Good:** `"1. Create a new branch named 'feature/user-auth-cache'. 2. Modify auth.py to add Redis caching to the get_user function. 3. Commit the change with the message 'feat(auth): add caching to get_user'."`
    *   **Bad:** `"Add caching and make a branch."`

## Don'ts: Common Pitfalls to Avoid

*   **DON'T Be Vague or Conversational.**
    Avoid ambiguity. The AI will take your instructions literally. Phrases like "make it better," "clean this up," or "I think maybe" lead to unpredictable results.

*   **DON'T Give Large, Undefined Repetitive Tasks.** (New Section)
    When you need the AI to perform the same action on many files, it can sometimes take a "lazy" shortcut and only process a few of them. You must be explicit to prevent this.
    *   **Bad (High Risk of Incomplete Work):** `"For EACH of the attached .persona.md files, your task is to write and add a concise, one-sentence description..."`
    *   **Good (More Reliable):** `"Next, you must process EACH of the following persona files that were attached: - core/arc-1.persona.md - core/csa-1.persona.md ... (list all files explicitly) ... For each file in the list above, your plan must add a concise, one-sentence description..."`
    *   **Why it's better:** Explicitly listing the items in the prompt forces the AI to acknowledge each one and makes it much harder for it to "forget" to complete the entire task.

*   **DON'T Mix "Thinking" and "Doing" in a Single Prompt.**
    The AI is best at one of two things: analyzing a situation OR generating a plan/artifact. Don't ask it to do both.
    *   **Good (Analysis):** `ai --persona core/arc-1 "Analyze these two files and tell me the key differences."`
    *   **Good (Generation):** `ai --persona core/csa-1 "Generate a plan to refactor file_A to be more like file_B."`
    *   **Bad:** `"Can you look at these files and figure out what's wrong, and then fix it and commit it?"`

*   **DON'T Rely on the AI for "Creative" Git Operations.**
    The AI is excellent at following a simple, procedural sequence like `branch -> change -> add -> commit`. It is not good at complex Git tasks like interactive rebasing, cherry-picking, or resolving merge conflicts.

*   **DON'T Assume the AI Remembers Things Outside the Current Context.**
    Unless you are using a `--session`, the AI has no memory of past runs. Each command is stateless. If a task requires knowledge from a previous run, you must either use a session or re-attach the relevant files.

## Advanced Techniques & Caveats

*   **Technique: The "Act As" Tactic for Missing Personas**
    If, and **only if**, a specialized persona for your specific, nuanced task does not exist, you can use the "Act As" tactic to provide a temporary, inline role. This is a fallback, not a replacement for using a proper persona.
    *   **Use Case:** You need a quick security review, but a full `patterns/sva-1` (Security Vulnerability Auditor) persona doesn't exist yet.
    *   **Example:** `ai --persona core/arc-1 "Analyze the attached auth.py file. **For this task, act as a senior security reviewer** and generate a report highlighting potential vulnerabilities like injection risks or improper error handling."`
    *   This works by layering a specific instruction *on top of* a capable base persona (`arc-1` is a good choice for analysis).

*   **Caveat: Negative Constraints are Unreliable.**
    Telling the AI "Do not include a push step" is less reliable than giving it a positive list of actions that simply omits the push step. It's better to specify exactly what you *do* want.

*   **Caveat: Large Inputs Can Reduce Reliability.**
    Very large context windows (many large files) can sometimes cause even good models to fail at generating perfect JSON plans or to produce incomplete logical plans. If a complex task fails, your first debugging step should be to try and simplify the prompt or break the task into smaller batches.