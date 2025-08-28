# Guide: Project-Specific Configuration (.ai_config.yml)

The `ai-assistant` becomes most powerful when it is deeply integrated with your project. The `.ai_config.yml` file is the key to this integration. By creating this file in your project's root directory, you can automate context injection and customize the assistant's behavior for everyone on your team.

This file acts as your project's **Configuration Manifest**, telling the assistant how to behave whenever it's run from within that directory.

## Core Use Cases

### 1. Automating Context with `auto_inject_files`

The `auto_inject_files` setting allows you to specify a list of "canonical documents" that are critical to your project. This feature serves two powerful, distinct purposes:

1.  **General Context Injection:** For any prompt, these files will be automatically attached to the context, ensuring the AI always has access to core information like architectural principles or agent definitions.

2.  **RAG Query Expansion (New Superpower):** When using the [Codebase-Aware RAG Workflow](./rag_workflow.md), the content of these files is used to provide high-level project context to an LLM. This allows the system to transform a simple user query (e.g., "fix auth bug") into a highly specific, project-aware search query (e.g., "debug AuthManager service OAuth2 token refresh error"). This dramatically improves the accuracy and relevance of RAG results.

```yaml
# .ai_config.yml

general:
  # These files will be automatically used for general context
  # AND to power the intelligent RAG query expansion.
  auto_inject_files:
    - "PROJECT_BLUEPRINT.md"
    - "AGENTS.md"

# Configure the connection to your shared OCI bucket
oracle_cloud:
  namespace: "your-oci-namespace"
  bucket: "your-oci-bucket-name"
  region: "your-oci-region"

tools:
  shell:
    # This list defines which shell commands the AI is allowed to plan.
    # For a read-only user, this can be an empty list.
    # For developers, you might add: ['ls', 'cat', 'grep', 'git']
    allowed_commands: []
```

### 2. Configuring the RAG Client
For teams using the [Codebase-Aware RAG Workflow](./rag_workflow.md), this file is used to configure the connection to the central OCI Object Storage bucket where indexes are stored.

```yaml
# .ai_config.yml

rag:
  # Enable branch-specific indexes (highly recommended)
  enable_branch_awareness: true
  
  # Configure the connection to your shared OCI bucket
  oracle_cloud:
    # The OCI namespace where your bucket resides
    namespace: "your-oci-namespace"
    # The name of the bucket storing the index archives
    bucket: "your-oci-bucket-name"
    # The OCI region for the bucket (e.g., eu-frankfurt-1)
    region: "your-oci-region"
    # (Optional) How long to cache the index locally, in hours. Default is 24.
    cache_ttl_hours: 24
```

## How to Create Your Configuration File

1.  **Create the File:** In the root directory of your project, create a new file named `.ai_config.yml`.
2.  **Add Configuration Sections:** Add the relevant sections (`general`, `rag`, etc.) as needed.
3.  **Commit the File:** Commit `.ai_config.yml` to your repository so that the entire team shares the same configuration.

This simple configuration is the single most effective step you can take to create a powerful, project-aware AI workflow.


> #### A Note on Configuration Integrity
>
> The AI Assistant uses a strict validation system to read its configuration. This ensures that all settings are correct and prevents unexpected behavior. If you upgrade the `ai-assistant` tool to a new version, its configuration requirements may change. If you see a `ValidationError` when running a command, it is a sign that your `.ai_config.yml` needs to be updated to match the new schema required by the tool.
