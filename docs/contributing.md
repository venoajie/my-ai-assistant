# Contributing Guide

We welcome contributions to the AI Assistant! This guide provides the information you need to get started, from governing personas to extending the tool with plugins.

## Persona Governance

This project enforces a strict structural standard for all persona files to ensure quality and consistency. All contributions that add or modify personas must pass our validation script.

### The Standard

The rules for persona frontmatter and body sections are defined in `src/ai_assistant/internal_data/persona_config.yml`. This file is the single source of truth for persona structure.

The persona directory structure is also a key part of governance. Please see the **[Persona System Guide](./personas.md#the-persona-directory-structure)** for a detailed explanation of the `_mixins`, `_base`, `core`, and `domains` directories.

### How to Validate Your Changes

Before submitting a pull request with persona changes, run the validation script from the project root:

```bash
python scripts/generate_manifest.py
```

This script serves two purposes:
1.  **Validation:** It acts as a linter, failing immediately if any persona file is malformed or does not match its canonical alias.
2.  **Generation:** If all personas are valid, it generates the `src/ai_assistant/internal_data/persona_manifest.yml` file.

You must commit the updated manifest along with your persona changes. Pull requests with stale or missing manifests will be blocked by CI checks.

---

## Extending the Assistant

To contribute effectively, it's important to understand the core data structures and extension points of the system.

-   **System Contracts:** The schemas for all major internal data objects (like Execution Plans and Output Packages) are formally defined in **[`system_contracts.yml`](./system_contracts.yml)**. Please consult this file before modifying any component that produces or consumes these structures.

-   **Plugins:** The assistant can be extended with custom context plugins. To learn how to build your own, please see the **[Extending with Plugins Guide](./plugins.md)**.