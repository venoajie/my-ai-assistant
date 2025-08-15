# AI Assistant: Your Command-Line Co-Pilot

For a detailed architectural overview, see [PROJECT_BLUEPRINT.md](PROJECT_BLUEPRINT.md).

Welcome to the AI Assistant, a general-purpose, command-line tool designed to be your collaborative partner in software development. It can help you write code, debug complex issues, review architecture, and automate repetitive tasks, all from the comfort of your terminal.

Built with a pluggable architecture, it can be extended with domain-specific knowledge for any field, from trading and finance to web development and data science.

## Key Features

-   **Conversational & Stateful:** Engage in interactive sessions where the assistant remembers the context of your work.
-   **Expert Persona System:** Instruct the assistant to adopt specialized expert profiles for higher-quality, consistent results.
-   **File System Integration:** The assistant can read, analyze, and write files, enabling it to perform meaningful development tasks.
-   **Decoupled Execution (New!):** A robust two-stage workflow separates AI-driven analysis from deterministic execution, enhancing safety and resilience.
-   **Pluggable Architecture:** Easily extend the assistant's knowledge with custom "Context Plugins".
-   **Autonomous Mode:** Grant the assistant the ability to execute multi-step plans without supervision (use with caution).
-   **Layered Configuration:** Flexible configuration system that scales from personal preferences to project-specific settings.
-   **Asynchronous Core:** Built with an `async` core for a responsive feel and future-readiness for parallel tasks.