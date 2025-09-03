# Guide: Project-Specific Configuration (.ai_config.yml)

The `ai-assistant` becomes most powerful when it is deeply integrated with your project. The `.ai_config.yml` file is the key to this integration. By creating this file in your project's root directory, you can customize the assistant's behavior for everyone on your team.

This file acts as your project's **Configuration Manifest**, telling the assistant how to behave whenever it's run from within that directory.

## Core Use Cases

### 1. Configuring the Codebase-Aware RAG Workflow

For teams using the [Codebase-Aware RAG Workflow](./rag_workflow.md), this file is where you configure the connection to the central **Librarian RAG Service**.

```yaml
# .ai_config.yml

rag:
  # The URL of your deployed Librarian service.
  librarian_url: "http://your-librarian-service-host:8000"

  # The API key for authenticating with the Librarian service.
  # It is HIGHLY recommended to set this via the LIBRARIAN_API_KEY environment variable
  # instead of committing it to the file.
  librarian_api_key: ${LIBRARIAN_API_KEY}

  # The number of final context chunks to request from the Librarian.
  rerank_top_n: 5
```

### 2. Automating Context with `auto_inject_files`

The `auto_inject_files` setting allows you to specify a list of "canonical documents" that are critical to your project. These files will be automatically attached to the context for any prompt, ensuring the AI always has access to core information like architectural principles or agent definitions.

```yaml
# .ai_config.yml

general:
  # These files will be automatically attached to every prompt.
  auto_inject_files:
    - "PROJECT_BLUEPRINT.md"
    - "AGENTS.md"
```

### 3. Securing the Shell Tool with `allowed_commands`

You can define a project-specific allowlist of shell commands that the AI is permitted to use. This is a critical security feature.

```yaml
# .ai_config.yml

tools:
  shell:
    # This list defines which shell commands the AI is allowed to plan.
    # For a read-only user, this can be an empty list.
    # For developers, a safe list might include: ['ls', 'cat', 'grep', 'git']
    allowed_commands: []
```

## How to Create Your Configuration File

1.  **Create the File:** In the root directory of your project, create a new file named `.ai_config.yml`.
2.  **Add Configuration Sections:** Add the relevant sections (`general`, `rag`, `tools`) as needed.
3.  **Commit the File:** Commit `.ai_config.yml` to your repository so that the entire team shares the same configuration. **Remember to add your `.env` file containing secrets to `.gitignore`!**