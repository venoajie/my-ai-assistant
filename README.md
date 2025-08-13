# AI Assistant: Your Command-Line Co-Pilot

Welcome to the AI Assistant, a general-purpose, command-line tool designed to be your collaborative partner in software development. It can help you write code, debug complex issues, review architecture, and automate repetitive tasks, all from the comfort of your terminal.

Built with a pluggable architecture, it can be extended with domain-specific knowledge for any field, from trading and finance to web development and data science.

## Key Features

-   **Conversational & Stateful:** Engage in interactive sessions where the assistant remembers the context of your work.
-   **Expert Persona System:** Instruct the assistant to adopt specialized expert profiles for higher-quality, consistent results.
-   **File System Integration:** The assistant can read, analyze, and write files, enabling it to perform meaningful development tasks.
-   **Pluggable Architecture:** Easily extend the assistant's knowledge with custom "Context Plugins".
-   **Autonomous Mode:** Grant the assistant the ability to execute multi-step plans without supervision (use with caution).
-   **Layered Configuration:** Flexible configuration system that scales from personal preferences to project-specific settings.
-   **Asynchronous Core:** Built with an `async` core for a responsive feel and future-readiness for parallel tasks.

## Installation

#### 1. For Stable Use
```bash
pip install my-ai-assistant
```

#### 2. For Development
If you want to contribute or modify the assistant's source code, install it in "editable" mode.
```bash
# First, clone the repository
git clone https://github.com/your-repo/my-ai-assistant.git
cd my-ai-assistant

# Install in editable mode
pip install -e .
```

---

## The Core Concept: Your First Command

Almost every interaction with the assistant follows a simple structure.

**Basic Structure:**
```bash
ai [FLAGS] "Your goal in plain English"
```
-   **`[FLAGS]`**: Optional switches that change the assistant's behavior.
-   **`"Your Goal..."`**: Your instruction to the assistant, enclosed in quotes.

### Your Main Controls: The Core Flags

| Flag | What It Does | Why You Use It |
| :--- | :--- | :--- |
| `--version` | Displays the installed version number. | To verify your installation. |
| `--new-session` | Starts a brand new, clean conversation. | **Use this for every new task.** It ensures the AI's memory is fresh. |
| `--session <ID>` | Resumes a previous conversation using its unique ID. | **Use this to continue a task** you started earlier. |
| `--persona <ALIAS>` | Makes the AI adopt a specific "expert" personality. | Personas provide expert-level instructions, leading to higher-quality results. **Highly recommended.** |
| `-f, --file <PATH>` | Attaches the content of a file to your request. Can be used multiple times. | Use this when the AI needs to **read, review, or modify one or more files**. |
| `--context <PLUGIN>` | Loads a domain-specific context plugin. | Use this to give the AI **specialized knowledge** about your project's domain. |
| `--autonomous` | Enables fully automatic mode; the AI will **not** ask for permission. | For well-defined tasks where you trust the AI to run without supervision. **Use with extreme caution.** |

## The Persona System: Your Team of Virtual Experts

Personas are the most powerful feature for ensuring high-quality, consistent, and structured output. When you use a persona, you are providing the AI with a detailed set of instructions, a "core philosophy," and an operational protocol, much like briefing a human expert for a specific task.

### How to Use Personas

Simply provide the persona's alias using the `--persona` flag. **The alias is always the full file path within the `personas` directory, without the `.persona.md` extension.**

```bash
# Use the Systems Architect from the 'core' category
ai --persona core/csa-1 "Design a multi-stage Dockerfile for a Python app."

# Use the Quantitative Trading Strategy Analyst from the 'domains/trading' category
ai --persona domains/trading/qtsa-1 "Develop a mean-reversion strategy for ETH/USDT."
```

### Discovering Available Personas

The definitive list of available expert personas is located in the `persona_manifest.yml` file at the root of the project. This file is the source of truth for the `core/si-1` (Session Initiator) persona and provides the alias, title, and a description of each expert's capability.

To regenerate this manifest after adding or changing personas, run the following command from the project root:

```bash
python scripts/generate_manifest.py
```

### Bundled Personas

Here is a list of the primary persona examples included with the assistant. These are concrete, expert agents you can use directly.

| Alias | Category | Title | Use Case |
| :--- | :--- | :--- | :--- |
| `core/csa-1` | Core | Systems Architect | Designs new systems or refactors existing ones, ensuring architectural integrity. |
| `core/dca-1` | Core | Documentation Architect | Creates clear, user-centric documentation from technical artifacts. |
| `core/dpa-1` | Core | Deployment Architect | Creates detailed, risk-mitigated deployment and validation plans. |
| `patterns/da-1` | Patterns | Debugging Analyst | Diagnoses the root cause of bugs from error reports and stack traces. |
| `patterns/bpr-1` | Patterns | Best Practices Reviewer | Acts as a senior peer reviewer for code quality, style, and patterns. |
| `patterns/qsa-1` | Patterns | Quality Strategy Architect | Analyzes a codebase to create a prioritized, risk-based testing plan. |
| `patterns/sva-1` | Patterns | Security Auditor | Reviews code with an adversarial mindset to find potential vulnerabilities. |
| `domains/trading/qtsa-1` | Domains | Quant Strategy Analyst | Guides the development of formal, testable trading strategy blueprints. |
| `domains/finance/ada-1` | Domains | API Contract Architect | Designs API contracts for financial services, focusing on REST and OpenAPI. |

### Creating Your Own Personas

You can easily create your own personas by placing `.persona.md` files in your user configuration directory: `~/.config/ai_assistant/personas/`.

For example, to create a new persona `my-patterns/dba-1`, you would create the file:
`~/.config/ai_assistant/personas/my-patterns/dba-1.persona.md`

The application will **always check your user directory first**, allowing you to override bundled personas or add your own without modifying the installed package.

## Getting Started: A Step-by-Step Workflow

This is the most common and powerful way to use the assistant.

#### Step 1: Start a New Task
Always begin a new, distinct task with `--new-session`.
```bash
ai --new-session --persona patterns/da-1 "I'm getting a 'KeyError' in my 'distributor' service. I think the problem is in 'src/distributor.py'. Can you help me debug it?"
```
The assistant will respond and give you a session ID: `✨ Starting new session: a1b2c3d4-e5f6-7890-gh12-i3j4k5l6m7n8`

#### Step 2: Continue the Conversation
Now, use the `--session` flag with the ID you just received. The AI will remember everything.
```bash
# The AI knows you are talking about the 'distributor' service and 'src/distributor.py'
ai --session a1b2c3d4-e5f6-7890-gh12-i3j4k5l6m7n8 "Okay, show me the contents of that file."
```

#### Step 3: Working with Multiple Files

For tasks that require context from multiple files, such as code reviews or refactoring, attach them with the `-f` flag.

```bash
ai "Compare these two service implementations and suggest which pattern is better." \
  -f src/services/auth_service.py \
  -f src/services/user_service.py
```
---

## Advanced Workflows


### Expert Mode: Autonomous Operation

This mode allows the assistant to complete an entire task—including making file changes and committing to Git—without asking for your approval at each step.

> **WARNING: Use with extreme caution.** In this mode, the agent can create, modify, and delete files and push to your Git repository without confirmation. Only use it for well-defined tasks where you fully trust the plan.

**Example: Autonomous Refactoring**
```bash
ai --new-session --persona core/csa-1 --autonomous \
  -f src/services/distributor.py \
  "Refactor the 'distributor' service in the attached file to improve its logging and add error handling. When done, commit the changes to a new git branch named 'refactor/distributor-logging'."
```
The assistant will perform all the steps and notify you when it has pushed the branch. Your only job is to review the resulting pull request.


### Using Context Plugins for Domain Knowledge
Plugins inject domain-specific knowledge into the conversation.
```bash
# Activate the Trading plugin to get context on trading-specific terms
ai --context Trading "Explain the typical data flow from a market data receiver to an executor."
```

#### Extending the Assistant: Creating a Custom Plugin

You can teach the assistant about your project's unique domain by creating a simple plugin.

1.  **Create the plugin file.** The file must be in the `src/plugins/` directory and follow the naming convention `[plugin_name]_plugin.py`. For a plugin named "DataScience", create `src/plugins/datascience_plugin.py`.

2.  **Define the plugin class.** The class name must be `[PluginName]ContextPlugin`.

    ```python
    # src/plugins/datascience_plugin.py
    from ai_assistant.context_plugin import ContextPluginBase
    from typing import List
    from pathlib import Path

    class DataScienceContextPlugin(ContextPluginBase):
        name = "DataScience"
        
        def __init__(self, project_root: Path):
            self.project_root = project_root

        def get_context(self, query: str, files: List[str]) -> str:
            if "dataframe" in query.lower() or "etl" in query.lower():
                return "<DataScienceKnowledge>This is some expert knowledge about my domain.</DataScienceKnowledge>"
            return ""
    ```

3.  **Use the plugin.**
    ```bash
    ai --context DataScience "Explain how to optimize this ETL process for a large pandas DataFrame."
    ```

---

## Configuration & API Key Management

The assistant uses a layered configuration system and requires API keys to function.

### API Key Setup (Required)
The recommended and most secure method is using environment variables.
```bash
# For Linux/macOS
export GEMINI_API_KEY="your-gemini-api-key"
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

### Configuration Layers
The assistant merges settings from three locations, in order of priority:
1.  **Project Config (`.ai_config.yml`)**: Place this in your project's root for project-specific settings. (Highest priority)
2.  **User Config (`~/.config/ai_assistant/config.yml`)**: For your personal preferences.
3.  **Package Defaults (`default_config.yml`)**: Bundled with the assistant. Do not edit this directly. (Lowest priority)

## For Contributors: Persona Governance

This project enforces a strict structural standard for all persona files to ensure quality and consistency. All contributions that add or modify personas must pass our validation script.

### The Standard

The rules for persona frontmatter and body sections are defined in `persona_config.yml` at the project root. This file is the single source of truth for persona structure.

### How to Validate Your Changes

Before submitting a pull request with persona changes, run the validation script from the project root:

```bash
python scripts/generate_manifest.py
```

This script serves two purposes:
1.  **Validation:** It acts as a linter, failing immediately if any persona file is malformed or does not match its canonical alias.
2.  **Generation:** If all personas are valid, it generates the `persona_manifest.yml` file.

You must commit the updated `persona_manifest.yml` along with your persona changes. Pull requests with stale or missing manifests will be blocked by CI checks.

> ### The Persona Inheritance System
>
> To ensure consistency and reduce duplication, personas are built on a powerful inheritance system. This allows new, specialized personas to inherit a common set of directives and philosophies.
>
> #### Universal Standards (`_mixins/`)
>
> The application can be configured to automatically apply a "universal base persona" to **every** persona that is loaded. This is defined by the `universal_base_persona` key in `config.yml` and points to a persona in the `_mixins/` directory. By default, all personas inherit from `_mixins/codegen-standards-1`, which enforces a consistent, structured output format.
>
> #### Base Personas (`_base/`)
>
> The `_base/` directory contains foundational "archetypes" that define a core operational philosophy (e.g., technical analysis vs. collaborative dialogue). Specialized personas should inherit from one of these bases to ensure they follow a proven interaction pattern.
>
> #### How to Use Inheritance
>
> To make a new persona inherit from a base, use the `inherits_from` key in its frontmatter. The loader will recursively build the full persona content.
>
> **Example: `core/csa-1.persona.md`**
> ```yaml
> ---
> # The alias MUST match the file path
> alias: core/csa-1
> # The inherited alias MUST also match its file path
> inherits_from: _base/bcaa-1
> # ... other frontmatter
> ---
> <SECTION:PRIMARY_DIRECTIVE>
> To design new systems...
> # ... specific directives for this persona
> ```
> In this example, `csa-1` will first be composed with the universal `_mixins/codegen-standards-1` mixin, and then its explicit parent `_base/bcaa-1` will be prepended to its own body, creating a complete, multi-layered expert agent.
```