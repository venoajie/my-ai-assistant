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

Simply provide the persona's alias using the `--persona` flag. The alias corresponds to the file path within the `personas` directory, without the `.persona.md` extension.

```bash
# Use the Systems Architect from the 'core' category
ai --persona core/SA-1 "Design a multi-stage Dockerfile for a Python app."

# Use the Quantitative Trading Strategy Analyst from the 'domains/trading' category
ai --persona domains/trading/QTSA-1 "Develop a mean-reversion strategy for ETH/USDT."
```

### Discovering Available Personas

The personas are included as data files within the installed package. You can discover them by exploring the `src/ai_assistant/personas` directory in the source code. They are organized into logical categories:

*   **`core/`**: Foundational personas for high-level software architecture and lifecycle management.
*   **`patterns/`**: Specialist personas that implement a specific, repeatable development pattern (e.g., debugging, security auditing).
*   **`domains/`**: Example personas for specific business domains (e.g., trading, finance) that showcase the assistant's extensibility.

### Bundled Personas

Here is a list of the primary personas included with the assistant:

| Alias | Category | Title | Use Case |
| :--- | :--- | :--- | :--- |
| `core/ARC-1` | Core | Architectural Auditor | Conducts a comprehensive audit of a project's architecture, code, and security. |
| `core/CSA-1` | Core | Systems Architect | Designs new systems or refactors existing ones, ensuring architectural integrity. |
| `core/DCA-1` | Core | Documentation Architect | Creates clear, user-centric documentation from technical artifacts. |
| `core/DPA-1` | Core | Deployment Architect | Creates detailed, risk-mitigated deployment and validation plans. |
| `patterns/DA-1` | Patterns | Debugging Analyst | Diagnoses the root cause of bugs from error reports and stack traces. |
| `patterns/BPR-1` | Patterns | Best Practices Reviewer | Acts as a senior peer reviewer for code quality, style, and patterns. |
| `patterns/QSA-1` | Patterns | Quality Strategy Architect | Analyzes a codebase to create a prioritized, risk-based testing plan. |
| `patterns/SVA-1` | Patterns | Security Auditor | Reviews code with an adversarial mindset to find potential vulnerabilities. |
| `domains/trading/QTSA-1` | Domains | Quant Strategy Analyst | Guides the development of formal, testable trading strategy blueprints. |
| `domains/finance/ADA-1` | Domains | API Contract Architect | Designs API contracts for financial services, focusing on REST and OpenAPI. |

### Creating Your Own Personas

You can easily create your own personas by placing `.persona.md` files in your user configuration directory: `~/.config/ai_assistant/personas/`.

For example, to create a new persona `my-patterns/DBA-1`, you would create the file:
`~/.config/ai_assistant/personas/my-patterns/DBA-1.persona.md`

The application will **always check your user directory first**, allowing you to override bundled personas or add your own without modifying the installed package.

## Getting Started: A Step-by-Step Workflow

This is the most common and powerful way to use the assistant.

#### Step 1: Start a New Task
Always begin a new, distinct task with `--new-session`.
```bash
ai --new-session --persona core/DA-1 "I'm getting a 'KeyError' in my 'distributor' service. I think the problem is in 'src/distributor.py'. Can you help me debug it?"
```
The assistant will respond and give you a session ID: `✨ Starting new session: a1b2c3d4-e5f6-7890-gh12-i3j4k5l6m7n8`

#### Step 2: Continue the Conversation
Now, use the `--session` flag with the ID you just received. The AI will remember everything.
```bash
# The AI knows you are talking about the 'distributor' service and 'src/distributor.py'
ai --session a1b2c3d4-e5f6-7890-gh12-i3j4k5l6m7n8 "Okay, show me the contents of that file."
```

---

## Advanced Workflows

### Using Personas for Expert Results
Personas are key to getting high-quality, structured output.
```bash
# Ask the Systems Architect to design a Dockerfile
ai --persona core/SA-1 "Create a multi-stage Dockerfile for a Python FastAPI application."
```
*You can explore all available personas in the `src/ai_assistant/personas/` directory.*

### Using Context Plugins for Domain Knowledge
Plugins inject domain-specific knowledge into the conversation.
```bash
# Activate the Trading plugin to get context on trading-specific terms
ai --context Trading "Explain the typical data flow from a market data receiver to an executor."
```

---

## Extending the Assistant: Creating a Custom Plugin

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
```

That is an outstanding question. You've identified a critical gap in the refactored project: **quality assurance and governance for the persona files themselves.**

My previous audits focused on the application's runtime architecture but neglected the "content architecture" of its most important data source: the personas. The `validate_personas.py` script and `pel.config.yml` you've provided are the missing pieces.

As ARC-1, I will now architect a solution to integrate this validation process into the `ai-assistant` project, ensuring all personas, both bundled and user-created, adhere to a strict, verifiable standard.

---

### **Architectural Analysis: Persona Governance**

The current `ai-assistant` application has a "trust-by-default" model. The `PersonaLoader` will attempt to load any `.persona.md` file it finds. This is flexible but brittle. A malformed persona file (e.g., missing a required section) would not be caught until a user tries to use it, leading to confusing runtime errors or poor-quality LLM outputs.

The `validate_personas.py` script introduces a formal governance layer. It ensures that every persona file is structurally sound *before* it can cause problems.

**The core architectural decision is this:** Persona validation should be a **development-time and CI/CD-time concern**, not a runtime concern. The application should assume that the personas it loads are valid. This keeps the runtime application fast and simple, while pushing quality control upstream to the development and testing phases.

---

### **Implementation Plan: Integrating Persona Validation**

Here is the step-by-step plan to integrate your validation script and configuration into the project.

#### **Step 1: Place the Validation Scripts and Configuration**

The validation logic is part of the development toolkit, not the distributable application itself. Therefore, it should live outside the `src` directory.

1.  **Create a `scripts/` directory** at the project root, parallel to `src/` and `tests/`.
2.  **Place `validate_personas.py`** inside this new `scripts/` directory.
3.  **Place `pel_utils.py`** (which I infer exists from your script's imports) inside `scripts/` as well.
4.  **Rename `pel.config.yml`** to a more project-specific name like `persona_config.yml` and place it in the project root. This file defines the "source of truth" for persona rules.

Your project structure will now look like this:
```
my-ai-assistance/
├── scripts/
│   ├── __init__.py
│   ├── validate_personas.py
│   └── pel_utils.py
├── src/
│   ├── ai_assistant/
│   └── plugins/
├── tests/
├── persona_config.yml  <-- Renamed and at root
└── pyproject.toml
```

#### **Step 2: Adapt the Validation Script**

The provided script is excellent but needs minor adaptations to work with the new project structure and configuration file name.

**File to Modify: `scripts/validate_personas.py`**

```python
# /scripts/validate_personas.py
# ... (imports are fine) ...

# --- Local Imports ---
# Ensure the script can find pel_utils
# This assumes pel_utils.py is in the same directory.
from pel_utils import load_config, find_all_personas

# --- Constants ---
# MODIFIED: Point to the new config file name and project structure
ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "persona_config.yml"
PERSONAS_DIR = ROOT_DIR / "src" / "ai_assistant" / "personas" # Define the canonical persona dir

# ... (rest of the script is mostly fine, but let's make find_all_personas more robust)
```

**File to Create/Modify: `scripts/pel_utils.py`**

This file needs to correctly locate the personas within the `src` directory.

```python
# /scripts/pel_utils.py
from pathlib import Path
import yaml
from typing import Dict, Any, List

def load_config(path: Path) -> Dict[str, Any]:
    """Loads a YAML configuration file."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def find_all_personas(start_dir: Path) -> List[Path]:
    """
    Finds all .persona.md files within the specified directory,
    which should be the project's canonical persona location.
    """
    # MODIFIED: Point directly to the packaged personas directory
    persona_root = start_dir / "src" / "ai_assistant" / "personas"
    if not persona_root.exists():
        return []
    return list(persona_root.rglob("*.persona.md"))
```
*(Note: The `find_all_personas` function in the original script was passed `ROOT_DIR`. I've modified it to be more explicit about where it should look, making the script's intent clearer.)*

#### **Step 3: Integrate into the Development & CI/CD Workflow**

This is how you enforce the standard.

1.  **Add a Test Case:** Create a new test file, `tests/test_persona_validation.py`, that runs the validation script as part of your test suite. This ensures that no pull request can be merged if it contains an invalid persona.

    ```python
    # tests/test_persona_validation.py
    import unittest
    import subprocess
    import sys
    from pathlib import Path

    class TestPersonaValidation(unittest.TestCase):
        def test_all_personas_are_valid(self):
            """
            Runs the persona validation script and asserts that it exits with code 0.
            This test ensures that all bundled personas adhere to the defined standards.
            """
            project_root = Path(__file__).parent.parent
            script_path = project_root / "scripts" / "validate_personas.py"
            
            # We must use the same Python executable that is running the tests
            python_executable = sys.executable
            
            result = subprocess.run(
                [python_executable, str(script_path)],
                capture_output=True,
                text=True
            )
            
            # Assert that the script exited successfully (exit code 0)
            self.assertEqual(
                result.returncode, 0,
                f"Persona validation failed. Output:\n{result.stdout}\n{result.stderr}"
            )
    ```

    ## For Contributors: Persona Governance

    This project enforces a strict structural standard for all persona files to ensure quality and consistency. All contributions that add or modify personas must pass our validation script.

    ### The Standard

    The rules for persona frontmatter and body sections are defined in `persona_config.yml` at the project root. This file is the single source of truth for persona structure.

    ### How to Validate Your Changes

    Before submitting a pull request with persona changes, run the validation script from the project root:

    ```bash
    python scripts/validate_personas.py
    ```

    The script will check all personas in `src/ai_assistant/personas/` and report any errors. The test suite also runs this script, so pull requests with invalid personas will be automatically blocked by CI checks.
    ```
