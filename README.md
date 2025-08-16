# AI Assistant: Your Command-Line Co-Pilot

Welcome to the AI Assistant, a general-purpose, command-line tool designed to be your collaborative partner in software development. It can help you write code, debug complex issues, review architecture, and automate repetitive tasks, all from the comfort of your terminal.

## Key Features

-   **Expert Persona System:** Instruct the assistant to adopt specialized expert profiles for higher-quality, consistent results.
-   **Decoupled & Safe Execution:** A robust two-stage workflow separates AI analysis from deterministic execution, enhancing safety and resilience.
-   **Adversarial Plan Validation:** Before execution, plans are reviewed by a skeptical AI critic to identify potential flaws and risks.
-   **Pluggable Architecture:** Easily extend the assistant's knowledge with custom "Context Plugins".
-   **Stateful Conversations:** Engage in interactive sessions where the assistant remembers the context of your work.
-   **Asynchronous Core:** Built with an `async` core for a responsive feel and future-readiness for parallel tasks.

## Installation

```bash
# For stable use
pip install my-ai-assistant

# For development
git clone https://github.com/your-repo/my-ai-assistant.git
cd my-ai-assistant
pip install -e .
```

---

## Your First Command

The assistant is controlled with a simple command structure. Here is a basic example to get you started:

```bash
# Ask the Debugging Analyst persona for help with a specific file
ai --new-session --persona patterns/da-1 \
  -f src/my_buggy_file.py \
  "I'm getting a 'KeyError' in this file. Can you help me find the cause?"
```

---

## Full Documentation

This README provides a brief overview. For detailed guides on getting started, advanced usage, and creating your own personas and plugins, please see our full documentation.

**[➡️ Read the Full Documentation Here](./docs/index.md)**

## For Contributors

Interested in contributing to the AI Assistant? We welcome your help! Please start by reading our **[Contributing Guide](./docs/contributing.md)**, which covers persona governance and explains the core data contracts of the system.
```
