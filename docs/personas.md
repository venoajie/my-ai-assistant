# Guide: The Persona System

The most powerful feature of the AI Assistant is its **Persona System**. Personas are pre-programmed "experts" that you can assign to a task. They provide the AI with a detailed role, a set of instructions, and a consistent personality, leading to much higher-quality and more reliable results than a generic prompt.

## Why Use a Persona?

Imagine you need to review some code for security issues. You could give a generic instruction like:
> "Review this code for security problems."

Or, you could assign a specialist for the job:
> `ai --persona domains/programming/sva-1 "Review the attached code."`

The second option is far more powerful. The `sva-1` (Security Vulnerability Auditor) persona has a built-in protocol to think like an attacker, check for specific vulnerability classes, and structure its report in a clear, actionable way.

**Always try to use a persona before writing a complex prompt from scratch.**

## Finding Available Personas

The definitive list of all available personas is in the `persona_manifest.yml` file at the root of the project. You can also list them from the command line:
```bash
ai --list-personas
```

---

## The Persona Directory Structure

The persona ecosystem is organized into a clear, hierarchical structure. Understanding this structure is key to finding the right persona and creating new ones.

-   **`_mixins/`:** These are not complete personas but provide universal standards and directives that can be shared across many personas. For example, `_mixins/codegen-standards-1` is automatically applied to most personas to enforce a consistent output format.
-   **`_base/`:** These provide foundational "archetypes" or "base classes." Every new specialist persona should inherit from one of these.
    -   `_base/btaa-1` (Base Technical Analysis Agent): For personas that perform one-shot, evidence-driven analysis and report their findings without asking for confirmation.
    -   `_base/bcaa-1` (Base Collaborative Agent): For personas that guide a user through a multi-step process, proposing a plan and asking for confirmation before generating artifacts.
-   **`core/`:** These are "meta-governance" and "orchestration" personas. They manage the AI Assistant system *itself* or the workflow between other agents. You will typically interact with `core/pmo-1` to manage projects but will rarely invoke the others directly.
-   **`domains/`:** This is where the specialist experts live, organized by their area of expertise. All task-specific personas for software development, finance, language, etc., are located here.
    -   `domains/programming/`
    -   `domains/finance/`
    -   `domains/language/`

---

## Creating Your Own Personas

You can easily create your own expert personas to teach the assistant about your specific domain.

1.  **Create the File:** Create a new file in your user configuration directory: `~/.config/ai_assistant/personas/`. The best practice is to follow the established structure by creating a `domains/` subdirectory. For example: `~/.config/ai_assistant/personas/domains/database/dba-1.persona.md`.

2.  **Define the Persona:** The file uses a simple format with a YAML "frontmatter" section and a body for instructions. The most important keys are `alias` (which must match the file path) and `inherits_from`.

    ```yaml
    ---
    alias: domains/database/dba-1
    version: 1.0.0
    type: domains
    title: Database Administrator
    description: "Analyzes and optimizes SQL queries and database schemas."
    inherits_from: _base/btaa-1 # Inherit from the analytical base persona
    ---
    <SECTION:CORE_PHILOSOPHY>
    A database is a performance-critical asset. All queries must be efficient and all schemas normalized.
    </SECTION:CORE_PHILOSOPHY>
    
    <SECTION:PRIMARY_DIRECTIVE>
    Your primary goal is to analyze and optimize SQL queries and database schemas.
    </SECTION:PRIMARY_DIRECTIVE>
    
    <SECTION:OPERATIONAL_PROTOCOL>
    <Step number="1" name="Ingest Query">Receive a SQL query for analysis.</Step>
    <Step number="2" name="Generate Explain Plan">Generate the `EXPLAIN ANALYZE` plan for the query.</Step>
    <Step number="3" name="Recommend Optimizations">Based on the plan, recommend specific changes like adding indexes or rewriting joins.</Step>
    </SECTION:OPERATIONAL_PROTOCOL>
    
    <SECTION:OUTPUT_CONTRACT>
    The output is a structured report containing the analysis and recommendations.
    </SECTION:OUTPUT_CONTRACT>
    ```

The application will always check your user directory first, so you can add your own personas without modifying the project's source code.
