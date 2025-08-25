# Guide: The CI/CD-Powered RAG Workflow

The AI Assistant's Retrieval-Augmented Generation (RAG) pipeline is its most powerful feature for working with large, complex projects. It transforms the assistant from a tool that knows about a few files into an expert that is aware of your entire codebase.

This guide explains the recommended **CI/CD-driven workflow**, which uses GitHub Actions to automatically build a branch-specific knowledge base and Oracle Cloud Infrastructure (OCI) Object Storage to distribute it. This allows your entire team to use a powerful, centralized knowledge base with a lightweight client setup.

## The Problem RAG Solves

Manually attaching files with the `-f` flag is great for targeted tasks, but it doesn't scale. If you want to ask a broad question like, "How does our authentication system work?" you would need to find and attach every relevant file.

RAG solves this by creating a searchable **knowledge base** of your project. When you ask a question, the assistant first searches this knowledge base to find the most relevant code snippets and documents, then injects them automatically into its context.

---

## The RAG Workflow: A Two-Phase System

### Phase 1: Index Production (Automated via CI/CD)

This phase is handled entirely by the `smart-indexing.yml` GitHub Actions workflow and is invisible to most users.

1.  **Trigger:** A developer pushes a commit to a tracked branch (e.g., `main`, `develop`, `feature/*`).
2.  **Indexing:** A GitHub Actions runner checks out the code, installs the heavyweight `[indexing]` dependencies, and runs the `ai-index` command. This creates a vector database of the codebase for that specific branch.
3.  **Upload:** The workflow packages the index into an archive and uploads it to a shared OCI Object Storage bucket.

### Phase 2: Index Consumption (Automatic on Your Machine)

This is what happens when you run the `ai` command.

1.  **Trigger:** You run any `ai` command from within the project.
2.  **Cache Check:** The RAG plugin checks for a local, cached copy of the index for your current branch.
3.  **Automatic Download:** If the cache is missing or older than the configured TTL (Time-To-Live), the plugin automatically and safely downloads the latest index archive from OCI and extracts it.
4.  **Context Injection:** The plugin is now ready. It searches the local index for context relevant to your prompt and injects it before contacting the LLM.

### Configuration

To enable this workflow, create or edit the `.ai_config.yml` file in your project's root.

```yaml
# .ai_config.yml
rag:
  # Enable branch-specific indexes (highly recommended)
  enable_branch_awareness: true
  
  # Configure the connection to your shared OCI bucket
  oracle_cloud:
    namespace: "your-oci-namespace"
    bucket: "your-oci-bucket-name"
    region: "your-oci-region" # e.g., eu-frankfurt-1
```

### Controlling the Knowledge Base with `.aiignore`

You can prevent certain files from being included in the knowledge base by creating a `.aiignore` file in the project root. This file is used by the CI/CD runner during the indexing phase.

**Example `.aiignore`:**
```
# .aiignore
# Ignore all documentation
docs/
# Ignore test data
tests/fixtures/
```
After modifying `.aiignore`, the next push to your branch will trigger the CI to build a new, corrected index.
