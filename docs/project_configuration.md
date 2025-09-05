# Guide: Project-Specific Configuration

The `ai-assistant` uses a powerful two-file system for configuration that separates behavior from secrets.

### The Configuration Model: `.env` and `.ai_config.yml`

1.  **`.env` (The Secrets File):**
    -   This file lives in your project root and contains secrets, API keys, and environment-specific URLs.
    -   It **MUST** be added to your `.gitignore` and should never be committed.
    -   It defines the **"what" and "where"** (e.g., `LIBRARIAN_API_URL`, `OPENAI_API_KEY`).

2.  **`.ai_config.yml` (The Behavior File):**
    -   This file also lives in your project root and defines the assistant's behavior for this project.
    -   It **SHOULD** be committed to your repository so the whole team shares the same settings.
    -   It defines the **"how"** (e.g., `auto_inject_files`, `allowed_commands`) and **references** secrets from the `.env` file using the `${...}` syntax.

This model provides a secure and flexible way to manage project-wide settings.


## Core Use Cases

### 1. Configuring the Codebase-Aware RAG Workflow

For teams using the [Codebase-Aware RAG Workflow](./rag_workflow.md), this file is where you configure the connection to the central **Librarian RAG Service**.

```yaml
# .ai_config.yml

rag:
  # The URL of your deployed Librarian service.
  librarian_url: ${LIBRARIAN_API_URL}

  # The API key for authenticating with the Librarian service.
  librarian_api_key: ${LIBRARIAN_API_KEY}

  
### 2. Configuring the RAG Indexer (for CI/CD)

For projects that are being indexed, this file tells the `ai-index` command how to connect to the central database and cloud storage. This configuration is used by the CI/CD pipeline.

```yaml
# .ai_config.yml (for an indexed project)

rag:
  # The connection URL for the central PostgreSQL database.
  database_url: ${DATABASE_URL}

  # Configuration for OCI Object Storage where manifests are stored.
  oracle_cloud:
    namespace: ${OCI_NAMESPACE}
    bucket: ${OCI_BUCKET}
    region: ${OCI_REGION}

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