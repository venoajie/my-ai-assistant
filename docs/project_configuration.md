# Guide: Project-Specific Configuration (.ai_config.yml)

The `ai-assistant` becomes most powerful when it is deeply integrated with your project. The `.ai_config.yml` file is the key to this integration. By creating this file in your project's root directory, you can automate context injection and customize the assistant's behavior for everyone on your team.

This file acts as your project's **Configuration Manifest**, telling the assistant how to behave whenever it's run from within that directory.

## Core Use Cases

### 1. Automating Context with `auto_inject_files`
The most common feature is `auto_inject_files`. It allows you to specify a list of "canonical documents" that will be automatically attached to **every single prompt** run within the project.

This is the best practice for ensuring the AI always has critical context, such as your project's architectural blueprint.

```yaml
# .ai_config.yml

general:
  # These files will be automatically attached to every prompt.
  auto_inject_files:
    - "PROJECT_BLUEPRINT.md"
    - "AGENTS.md"
```

### 2. Configuring the RAG Client
For teams using the [Codebase-Aware RAG Workflow](./rag_workflow.md), this file is used to configure the connection to the central indexing server.

```yaml
# .ai_config.yml

rag:
  # The IP address or hostname of the machine running the ChromaDB server
  chroma_server_host: "192.168.1.100"
  # The port the server is running on
  chroma_server_port: 8000
```

## How to Create Your Configuration File

1.  **Create the File:** In the root directory of your project, create a new file named `.ai_config.yml`.
2.  **Add Configuration Sections:** Add the relevant sections (`general`, `rag`, etc.) as needed.
3.  **Commit the File:** Commit `.ai_config.yml` to your repository so that the entire team shares the same configuration.

This simple configuration is the single most effective step you can take to create a powerful, project-aware AI workflow.
