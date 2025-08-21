# Contributing Guide

We welcome contributions to the AI Assistant! This guide provides the information you need to get started, from governing personas to extending the tool with plugins.

## Core Requirements

-   **Python Version:** Python 3.10 or higher is **required**.
-   **Reason:** The project relies on modern dependencies (e.g., `instructor`) that use typing syntax (`|` for unions) introduced in Python 3.10. The application will not run on older versions.

## Persona Governance

This project enforces a strict structural standard for all persona files to ensure quality and consistency. All contributions that add or modify personas must pass our validation script.

### The Standard
The rules for persona frontmatter and body sections are defined in `src/ai_assistant/internal_data/persona_config.yml`.

### How to Validate Your Changes
Before submitting a pull request with persona changes, run the validation script from the project root:
```bash
python scripts/generate_manifest.py
```
You must commit the updated `persona_manifest.yml` along with your persona changes. Pull requests with stale or missing manifests will be blocked by CI checks.

---

## Documentation-as-Code Workflow

To prevent drift between the application's behavior and its documentation, some documentation files are generated from templates and a central `governance.yml` file.

### The Workflow
1.  **Identify the Source:** If you need to change a rule (e.g., add a risky keyword), edit the source of truth: `src/ai_assistant/internal_data/governance.yml`. If you need to change the text of a guide, edit the corresponding file in `docs/templates/`.
2.  **Run the Generator:** After editing the source, run the documentation generator script locally:
    ```bash
    python scripts/generate_docs.py
    ```
3.  **Commit Both Source and Output:** You must commit your changes to the source file (e.g., the template) **and** the final generated Markdown file (e.g., `docs/prompting_guide.md`). The CI pipeline is configured to verify that the committed Markdown is perfectly in sync with the source templates, and it will fail if they do not match.

---

## Extending the Assistant

-   **System Contracts:** The schemas for all major internal data objects are formally defined in **[`system_contracts.yml`](./system_contracts.yml)**.
-   **Plugins:** To learn how to build your own plugins, please see the **[Extending with Plugins Guide](./plugins.md)**.
