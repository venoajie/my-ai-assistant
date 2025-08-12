
### **File: `README.md` (FINAL)**

# AI Assistant: Your Command-Line Co-Pilot

Welcome to the AI Assistant, a general-purpose, command-line tool designed to be your collaborative partner in software development. It can help you write code, debug complex issues, review architecture, and automate repetitive tasks, all from the comfort of your terminal.

Built with a pluggable architecture, it can be extended with domain-specific knowledge for any field, from trading and finance to web development and data science.

## Key Features

-   **Conversational & Stateful:** Engage in interactive sessions where the assistant remembers the context of your work.
-   **Expert Persona System:** Instruct the assistant to adopt specialized expert profiles for higher-quality, consistent results.
-   **File System Integration:** The assistant can read, analyze, and write files, enabling it to perform meaningful development tasks.
-   **Pluggable Architecture:** Easily extend the assistant's knowledge with custom "Context Plugins" for your specific domain.
-   **Autonomous Mode:** Grant the assistant the ability to execute multi-step plans without supervision for full task automation (use with caution).
-   **Layered Configuration:** Flexible configuration system that scales from personal preferences to project-specific settings.

## Installation

You can install the assistant using pip.

#### 1. For Stable Use

This is the recommended method for general use.
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

Almost every interaction with the assistant follows a simple structure. Mastering this is key to using the tool effectively.

**Basic Structure:**
```bash
ai [FLAGS] "Your goal in plain English"
```
-   **`[FLAGS]`**: Optional switches that change the assistant's behavior (e.g., `--new-session`).
-   **`"Your Goal..."`**: The most important part—your instruction to the assistant, enclosed in quotes.

### Your Main Controls: The Core Flags

These flags are your primary way to control the assistant's behavior.

| Flag | What It Does | Why You Use It |
| :--- | :--- | :--- |
| `--new-session` | Starts a brand new, clean conversation. | **Use this for every new task.** It ensures the AI's memory is fresh and not influenced by previous, unrelated work. |
| `--session <ID>` | Resumes a previous conversation using its unique ID. | **Use this to continue a task** you started earlier. The AI will remember the entire conversation history. |
| `--persona <ALIAS>` | Makes the AI adopt a specific "expert" personality. | Personas provide expert-level instructions, leading to higher-quality results. It's like choosing a specialist over a generalist. **Highly recommended.** |
| `-f, --file <PATH>` | Attaches the content of a file to your request. Can be used multiple times. | Use this when the AI needs to **read, review, or modify one or more files** to complete your goal. |
| `--context <PLUGIN>` | Loads a domain-specific context plugin. | Use this to give the AI **specialized knowledge** about your project's domain (e.g., Trading, Web, Finance). |
| `--autonomous` | Enables fully automatic mode; the AI will **not** ask for permission. | For well-defined tasks where you trust the AI to run without supervision. **Use with extreme caution.** |

---

## Getting Started: A Step-by-Step Workflow

This is the most common and powerful way to use the assistant. A "session" gives the AI a memory of your conversation.

#### Step 1: Start a New Task

Always begin a new, distinct task with `--new-session`. Let's ask for help debugging a service.

```bash
ai --new-session --persona core/DA-1 "I'm getting a 'KeyError' in my 'distributor' service. I think the problem is in 'src/distributor.py'. Can you help me debug it?"
```

The assistant will respond and, crucially, give you a session ID:
```text
✨ Starting new session: a1b2c3d4-e5f6-7890-gh12-i3j4k5l6m7n8
```

#### Step 2: Continue the Conversation

Now, you can ask follow-up questions using the `--session` flag with the ID you just received. The AI will remember everything you've discussed.

```bash
# The AI knows you are talking about the 'distributor' service and 'src/distributor.py'
ai --session a1b2c3d4-e5f6-7890-gh12-i3j4k5l6m7n8 "Okay, show me the contents of that file."
```

You can continue this back-and-forth until your task is complete. The session saves automatically after each turn.

---

## Leveling Up: Advanced Workflows

Once you're comfortable with sessions, you can start leveraging the assistant's more powerful features.

### Working with Multiple Files

For tasks that require context from multiple files, such as code reviews or refactoring, attach them with the `-f` flag.

```bash
ai "Compare these two service implementations and suggest which pattern is better." \
  -f src/services/auth_service.py \
  -f src/services/user_service.py
```

### Using Personas for Expert Results

Personas are pre-defined instruction sets that make the assistant act like a specialist. This is key to getting high-quality, structured output.

| Alias | Specialty | Use Case |
| :--- | :--- | :--- |
| `core/SA-1` | Systems Architecture | Designing services, Dockerfiles, IaC. |
| `domains/trading/QTSA-1` | Trading | Developing quantitative trading strategies. |

**Example:**
```bash
# Ask the Systems Architect to design a Dockerfile
ai --persona core/SA-1 "Create a multi-stage Dockerfile for a Python FastAPI application."
```
*You can explore all available personas in the `ai_assistant/personas/` directory.*

### Using Context Plugins for Domain Knowledge

Plugins inject domain-specific knowledge into the conversation, making the assistant "smarter" about your project's field.

**Example:**
```bash
# Activate the Trading plugin to get context on trading-specific terms
ai --context Trading "Explain the typical data flow from a market data receiver to an executor."
```

---

## Expert Mode: Autonomous Operation

This mode allows the assistant to complete an entire task—including making file changes and committing to Git—without asking for your approval at each step.

> **WARNING: Use with extreme caution.** In this mode, the agent can create, modify, and delete files and push to your Git repository without confirmation. Only use it for well-defined tasks where you fully trust the plan.

**Example: Autonomous Refactoring**
```bash
ai --new-session --persona core/SA-1 --autonomous \
  -f src/services/distributor.py \
  "Refactor the 'distributor' service in the attached file to improve its logging and add error handling. When done, commit the changes to a new git branch named 'refactor/distributor-logging'."
```
The assistant will perform all the steps and notify you when it has pushed the branch. Your only job is to review the resulting pull request.

---

## Extending the Assistant: Creating a Custom Plugin

You can teach the assistant about your project's unique domain by creating a simple plugin.

#### Step 1: Create the Plugin File

In the project's `plugins/` directory, create a new Python file. The name must follow the pattern `[plugin_name]_plugin.py`. For a plugin named "DataScience", create `plugins/datascience_plugin.py`.

#### Step 2: Write the Plugin Class

Inside your new file, define a class that inherits from `ContextPluginBase`. The class name must be `[PluginName]ContextPlugin`.

```python
# plugins/datascience_plugin.py
from ai_assistant.context_plugin import ContextPluginBase
from typing import List
from pathlib import Path

class DataScienceContextPlugin(ContextPluginBase):
    name = "DataScience"
    
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def get_context(self, query: str, files: List[str]) -> str:
        # Check for keywords related to your domain
        if "dataframe" in query.lower() or "etl" in query.lower():
            return """
<DataScienceKnowledge>
- ETL: Stands for Extract, Transform, Load. A common pattern for data pipelines.
- Pandas DataFrame: The primary in-memory data structure for data manipulation in Python.
- Scikit-learn: The standard library for machine learning models.
</DataScienceKnowledge>
"""
        return ""
```

#### Step 3: Use Your New Plugin

You can now activate your plugin using the `--context` flag.

```bash
ai --context DataScience "Explain how to optimize this ETL process for a large pandas DataFrame."
```

---

## Configuration & API Key Management

The assistant uses a layered configuration system and requires API keys to function.

### API Key Setup (Required)

The assistant needs API keys for providers like Google (Gemini) and DeepSeek. **The recommended and most secure method is using environment variables.**

1.  Get your API keys from the respective provider websites.
2.  Set them as environment variables in your shell. The names must match what's in the configuration (`default_config.yml`).

    ```bash
    # For Linux/macOS
    export GEMINI_API_KEY="your-gemini-api-key"
    export DEEPSEEK_API_KEY="your-deepseek-api-key"

    # For Windows (Command Prompt)
    set GEMINI_API_KEY="your-gemini-api-key"
    set DEEPSEEK_API_KEY="your-deepseek-api-key"
    ```
> **Security Best Practice:** Never commit API keys directly into code or configuration files. Use environment variables or a secure secret management tool.

### Configuration Layers

The assistant merges settings from three locations, in order of priority:

1.  **Project Config (`.ai_config.yml`)**: Place this in your project's root for project-specific settings. (Highest priority)
2.  **User Config (`~/.config/ai_assistant/config.yml`)**: For your personal preferences and API key overrides.
3.  **Package Defaults (`default_config.yml`)**: Bundled with the assistant. Do not edit this directly. (Lowest priority)

---

## Troubleshooting

| Symptom | Solution |
| :--- | :--- |
| **Missing API keys error** | Ensure you have set the required environment variables (e.g., `GEMINI_API_KEY`) and that the names match the `api_key_env` fields in your config. |
| **Session not found** | Double-check the session ID. If you've changed the `sessions_directory` in your config, ensure it points to the correct location. |
| **Plugin not loading** | Verify your plugin file is in the `plugins/` directory and follows the naming convention (e.g., `trading_plugin.py` for `--context Trading`). Check for typos. |
| **File attachment failed** | Make sure the file exists and the path is correct relative to your current working directory. |
```