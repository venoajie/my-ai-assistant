# Guide: The AI Assistant Safety Model

This document explains the safety-first design principles that govern how the AI Assistant interacts with your file system. Understanding this model is critical for using the tool safely and effectively.

## The First Principle: The AI is a Tool, Not an Oracle

> **CRITICAL: The AI can and will make mistakes.**

The AI Assistant is a powerful tool for automating tasks, but it is not infallible. It can misinterpret your intent, hallucinate facts, generate incorrect code, or produce plans that have unintended side effects.

**You, the user, are the final and most important part of the safety system.** Your role is to act as a skeptical reviewer. Always read the AI's proposed plan and the adversarial critique carefully before granting approval. You are ultimately responsible for the actions performed on your system.

The mechanisms described below are designed to give you the information and control you need to make informed decisions.

## Legal Disclaimer

This software is provided on an "AS IS" basis. The author assumes no liability for any damages, data loss, or other incidents caused by its operation. By using this software, you accept full responsibility for its outcomes. For the complete legal terms, refer to the [NOTICE](../../NOTICE) file.

---

## User Responsibility for Content and Actions

> **You are responsible for what you ask the AI to do and how you use what it creates.**

The AI will attempt to fulfill the instructions it is given. It does not have a moral compass or an understanding of legal boundaries. Therefore, the responsibility for using the tool ethically and lawfully rests entirely with you.

-   **Do not ask it to create harmful content:** Do not use this tool to generate malware, phishing emails, discriminatory content, or to perform any other malicious or illegal activity.
-   **You own the output:** You are responsible for the code and content generated from your prompts. If you use the AI to write code that causes damage to a third-party system, you are responsible for those damages.

The safety features of this tool are designed to prevent accidental self-inflicted harm. They are not designed to prevent intentional misuse. By using this software, you agree to the terms laid out in the [NOTICE](../../NOTICE) file.

---

## Data Privacy Warning

> **Your code, prompts, and attached file contents will be sent to third-party API providers.**

The AI Assistant functions by sending data to external Large Language Model (LLM) providers (e.g., Google, DeepSeek, OpenAI). This means that any information you include in a prompt or attach via the `-f` flag will leave your local machine and be processed on their servers.

-   **Do not send sensitive data:** This includes passwords, private keys, personally identifiable information (PII), or any proprietary source code you are not authorized to share.
-   **Review provider policies:** You are subject to the terms of service and privacy policies of the third-party LLM provider whose API key you are using.

The AI Assistant application itself does not store or log your prompt data, but it cannot control what happens to the data once it is sent to the external provider.

---

## The System's Safety Contract

The AI Assistant operates on a fundamental "Safety Contract" with you, the user:

> **The AI is only ever allowed to *propose* changes. The user must always give explicit, manual approval before any of those changes are applied to the local file system or Git repository.**

This contract is non-negotiable and is enforced by two primary mechanisms.

### Mechanism 1: The Two-Stage Workflow (Recommended)

This is the standard, safest, and **highly recommended** workflow for any task that modifies files. It provides a robust air gap between the AI's "thinking" and the actual execution.

**How it Works:**

1.  **You Use `--output-dir`:** When you include the `--output-dir <path>` flag in your command, you activate this safe mode.
2.  **AI Writes to a Sandbox:** When the AI's plan includes a `write_file` or other modification step, the action is **not** performed on your source code. Instead, the new or modified file is written into a temporary, sandboxed `./workspace/` directory inside your specified output path.
3.  **You Review the Plan:** The system generates a human-readable `summary.md` and a machine-readable `manifest.json`. You can review these to understand exactly what the AI intends to do. You can even use `diff` to compare the proposed files in the `workspace/` with your original files. This is your **manual review and approval gate**.
4.  **You Execute with `ai-execute`:** Only after you have reviewed and approved the plan do you run the separate, deterministic `ai-execute <path> --confirm` command. This non-AI script reads the manifest and safely applies the changes (e.g., copying files from the workspace, running Git commands).

This workflow gives you complete control and transparency, perfectly aligning with best practices like reviewing changes before committing them to a Git branch.

**Best Practice Example:**
A prompt to the AI should include the Git operations as part of the plan.
```bash
# The AI will generate a plan that includes creating a branch AND writing the file.
ai --persona domains/programming/csa-1 --output-dir ./ai_runs/my-refactor \
  -f src/main.py \
  "<ACTION>Refactor this file for clarity. The plan should create a new branch named 'refactor/main-clarity' before writing the file.</ACTION>"

# After reviewing the package, you execute the entire safe sequence.
ai-execute ./ai_runs/my-refactor --confirm
```

---

### Mechanism 2: Live Mode Safeguards (Discouraged)

If you choose to bypass the recommended workflow and run a modification task in "live mode" (i.e., without `--output-dir`), a secondary safety net is activated.

**How it Works:**

1.  **Risky Tool Detection:** Tools like `write_file` and `run_shell` are internally flagged as `is_risky: True`.
2.  **Adversarial Critique:** When the `kernel` sees a plan involving a risky tool, it automatically triggers an adversarial validation step. A skeptical "critic" persona reviews the plan for flaws.
3.  **Explicit Confirmation Prompt:** The system then **halts execution**. It will print the adversarial critique to your terminal—highlighting critical keywords in red to draw your attention to specific risks—and present you with a direct confirmation prompt:
    ```
    --- 🧐 ADVERSARIAL CRITIQUE ---
    - **Risk:** The `write_file` command will directly modify a file in the working directory.
    ----------------------------
          Proceed? [y/N]: 
    ```
The system **will not proceed** with the file modification unless you manually type `y` and press Enter. **If you type `N` or anything else, the entire task will be aborted immediately, and no further actions—including the final synthesis step—will be performed.**
