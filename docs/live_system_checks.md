# Guide: Performing Live System Checks

This guide explains how to use the AI Assistant's "live execution mode" to safely check the status of running applications or system services.

## Use Case: Read-Only Diagnostics

While the [Two-Stage Workflow](./getting_started.md) is the required method for any task that **modifies** files, live mode is well-suited for **read-only** diagnostic tasks, such as:
-   Checking the status of Docker containers.
-   Listing running processes.
-   Checking the available disk space.
-   Tailing the last few lines of a log file.

In this mode, the AI generates a plan to run a command, you approve it, and the AI then interprets the command's output for you.

---

## Built-in Safeguards & Best Practices

The `run_shell` tool has two critical, non-configurable safeguards to protect against the primary risks of live execution: hanging processes and excessive token consumption.

### 1. Command Timeout (Prevents Hanging)
Any command executed by the assistant has a **hardcoded 60-second timeout**. If the command does not complete within this time, it is automatically terminated, and an error is returned to the AI. This ensures that a hanging or long-running process can never cause the AI assistant itself to become unresponsive.

### 2. Output Truncation (Prevents Token Overruns)
The tool will only ever capture a maximum of **10,000 characters of standard output** and **10,000 characters of standard error**. If a command produces more output than this, it will be truncated. This acts as a vital circuit breaker to prevent unexpectedly large outputs (e.g., from a verbose log file) from causing a massive and expensive API call.

### Best Practices Summary
-   **DO** use specific, non-interactive commands that are expected to complete quickly (e.g., `docker ps`, `ls -l`, `df -h`).
-   **DON'T** use commands that are interactive or wait for user input (e.g., `ssh`, `python` interactive shell).
-   **DON'T** use commands that are designed to run indefinitely (e.g., `tail -f`, `watch`). The timeout will terminate them.
-   **BE AWARE** that if you are analyzing a very large file, the output will be truncated. For large files, it is better to attach them directly with the `-f` flag.

---

## The Safety Mechanism: Always in Control

Even with these safeguards, the system's [Safety Model](./safety_model.md) protects you. Any plan that uses `run_shell` will **always** halt and ask for your explicit manual approval before any command is executed. If you approve the plan by typing `y`, the command runs. **If you deny the plan by typing `N`, the entire task is aborted instantly, and the AI will not proceed to synthesize a final answer.**

---

## Walkthrough: Checking Docker Container Status

Let's walk through the exact scenario of asking the AI to check if Docker is running properly. The best persona for this kind of diagnostic task is the **Systems Integrity Analyst (`sia-1`)**.

### Step 1: Ask the Question

You start a session and ask your question in plain English.

**Your Command:**
```bash
ai --persona patterns/sia-1 "Can you check if my Docker containers are running correctly? List any containers that are stopped or have exited."
```

### Step 2: Review and Approve the Plan

The AI will determine that it needs to run a shell command to answer your question. Because `run_shell` is a risky tool, the system will halt and present you with the plan and a confirmation prompt.

**Terminal Output:**
```text
🚀 Executing adaptive plan...
  - Executing Step 1: run_shell({'command': 'docker ps -a'})

--- 🧐 ADVERSARIAL CRITIQUE ---
- **Risk:** The `run_shell` command will be executed directly in the current environment. While `docker ps -a` is a read-only command, always verify the command before proceeding.
----------------------------
      Proceed? [y/N]: 
```
This is your safety gate. The command `docker ps -a` is exactly what you'd expect. You can safely approve it.

**Your Input:**
```text
y
```

### Step 3: Receive the Synthesized Answer

After you approve, the system executes the `docker ps -a` command and captures its output. It then provides this output to the AI, which interprets it and gives you a clear, natural-language answer.

**Final Terminal Output:**
```text
============================================================
### Analysis
Based on the output of the `docker ps -a` command, there are three containers on the system. Two are running correctly, and one has exited.

### Findings
-   **Running Containers:**
    -   `postgres:14-alpine` (Status: Up 2 hours)
    -   `redis:latest` (Status: Up 2 hours)
-   **Stopped Containers:**
    -   `my-app:latest` (Status: Exited (1) 5 minutes ago)

**Recommendation:** The `my-app` container has exited with an error code (1). You may want to inspect its logs using the command `docker logs <container_id>`.
============================================================
```

This workflow allows you to use the power of the AI to not only run commands but to interpret their results, turning complex terminal output into actionable insights, all while keeping you in complete control.
