# Guide: Project-Specific Configuration (.ai_config.yml)

The `ai-assistant` becomes most powerful when it is deeply integrated with your project. The `.ai_config.yml` file is the key to this integration. By creating this file in your project's root directory, you can automate context injection and customize the assistant's behavior for everyone on your team.

This file acts as your project's **Configuration Manifest**, telling the assistant how to behave whenever it's run from within that directory.

## Core Use Case: Automating Context

The most common and powerful feature of this file is the `auto_inject_files` directive. It allows you to specify a list of "canonical documents" that will be automatically attached to **every single prompt** run within the project.

This is the best practice for ensuring the AI always has the most critical context, such as your project's architectural blueprint or a list of operational commands.

### Example: The "My Trading App" Best Practice

A well-configured project might have a `.ai_config.yml` file that looks like this:

```yaml
# .ai_config.yml

general:
  # These files will be automatically attached to every prompt.
  auto_inject_files:
    - "PROJECT_BLUEPRINT.md"
    - "AMBIGUITY_REPORT.md"
    - "AGENTS.md"
    - "etc"
```

**What this achieves:**

-   When a developer runs any `ai` command, the contents of these three critical files are automatically loaded into the AI's context.
-   This eliminates the need to manually attach them with `-f` flags for every command, saving time and preventing errors.
-   It guarantees that all AI agents (and all team members) are operating from the same, consistent source of truth.

## How to Create Your Configuration File

1.  **Create the File:** In the root directory of your project, create a new file named `.ai_config.yml`.

2.  **Add the `auto_inject_files` Section:** Start by adding the `general` and `auto_inject_files` keys.

3.  **List Your Canonical Files:** Add the paths to the files you want to be automatically included. These paths should be relative to your project's root directory.

This simple configuration is the single most effective step you can take to create a powerful, project-aware AI workflow.

## Putting It All Together: A Complete Example

The true power of the AI Assistant is unlocked when you combine project configuration, local personas, and local plugins. Here is what a best-practice setup looks like in a project's `.ai/` directory:

```
.ai/
├── plugins/
│   └── my_project_plugin.py  # Provides project-specific knowledge
└── personas/
    └── domains/
        └── my_project/
            └── data_analyst-1.persona.md # A project-specific expert
```

With this structure, you can create a `.ai_config.yml` that automatically injects your project's most important documents. This creates a powerful foundation where any developer on your team can easily call the right expert (`--persona`) with the right knowledge (`--context`) and the right architectural context (`auto_inject_files`) for any given task.
