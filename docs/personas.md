<!-- FILENAME: docs/personas.md -->

# Guide: The Persona System

The most powerful feature of the AI Assistant is its **Persona System**. Personas are pre-programmed "experts" that you can assign to a task. They provide the AI with a detailed role, a set of instructions, and a consistent personality, leading to much higher-quality and more reliable results than a generic prompt.

## Why Use a Persona?

Imagine you need to review some code for security issues. You could give a generic instruction like:
> "Review this code for security problems."

Or, you could assign a specialist for the job:
> `ai --persona patterns/sva-1 "Review the attached code."`

The second option is far more powerful. The `sva-1` (Security Vulnerability Auditor) persona has a built-in protocol to think like an attacker, check for specific vulnerability classes (like injection attacks or improper error handling), and structure its report in a clear, actionable way.

**Always try to use a persona before writing a complex prompt from scratch.**

## Finding Available Personas

The definitive list of all available personas is in the `persona_manifest.yml` file at the root of the project.

You can also list them from the command line:
```bash
ai --list-personas
```

## Creating Your Own Personas

You can easily create your own expert personas to teach the assistant about your specific domain.

1.  **Create the File:** Create a new file in your user configuration directory: `~/.config/ai_assistant/personas/`. You can create subdirectories for organization. For example, to create a persona for database administration, you might create: `~/.config/ai_assistant/personas/my-domain/dba-1.persona.md`.

2.  **Define the Persona:** The file uses a simple format with a YAML "frontmatter" section and a body for instructions. The most important keys are `alias` (which must match the file path) and `inherits_from` (which tells it which base personality to use).

    ```yaml
    ---
    alias: my-domain/dba-1
    title: Database Administrator
    inherits_from: _base/btaa-1 # Use btaa-1 for analytical tasks
    ---
    <SECTION:PRIMARY_DIRECTIVE>
    Your primary goal is to analyze and optimize SQL queries and database schemas...
    </SECTION:PRIMARY_DIRECTIVE>
    ```

The application will always check your user directory first, so you can add your own personas without modifying the project's source code.
```
<!-- FILENAME: docs/plugins.md -->
```markdown
# Guide: Extending the Assistant with Plugins

*This guide is a placeholder and will be expanded in a future version.*

This document will explain the plugin architecture and provide a step-by-step tutorial for creating your own custom context plugins to inject domain-specific knowledge into the AI Assistant.
```
