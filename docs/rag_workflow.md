# Guide: Setting Up Codebase-Aware Context (RAG)

The AI Assistant's Retrieval-Augmented Generation (RAG) pipeline is its most powerful feature for working with large, complex projects. It transforms the assistant from a tool that knows about a few manually attached files into an expert that is aware of your **entire codebase**.

This guide will walk you through setting up this workflow for your own project.

## The Problem RAG Solves

Manually attaching files with the `-f` flag is great for targeted tasks, but it doesn't scale. If you want to ask a broad question like, "How does our authentication system work?" you would need to find and attach every relevant file yourself.

RAG solves this by creating a searchable **knowledge base** of your project. When you ask a question, the assistant first searches this knowledge base to find the most relevant code snippets and documents, then automatically injects them into its context before contacting the AI.

---

## How It Works: The Two-Phase System

The RAG pipeline is designed for a robust team environment and operates in two distinct phases:

1.  **Phase 1: Index Production (Automated via CI/CD)**
    This is the "heavy lifting" phase, typically handled by an automated process like GitHub Actions. On every `git push`, the CI/CD system checks out the code, scans it, and uses powerful machine learning models to create a vector database—the "index"—of your project for that specific branch. This index is then packaged and uploaded to a shared cloud object store (like OCI Object Storage).

2.  **Phase 2: Index Consumption (Automatic on Your Machine)**
    This is the lightweight phase that happens when you run the `ai` command. It now includes an intelligent pre-processing step.

    **A. Intelligent Query Expansion (New)**
    Before searching, the system uses the high-level documents defined in your project's `auto_inject_files` (see the **[Configuration Guide](./project_configuration.md)**) to transform your simple query into a project-specific one. This bridges the gap between your intent and the technical keywords in the code.

    **B. Retrieval and Caching**
    The RAG plugin uses the expanded query to search the knowledge base. It automatically detects your current project and branch, checks for a local copy of the index, and if it's missing or out of date, downloads the latest version from shared cloud storage.

    **C. Optional Reranking**
    To maximize accuracy, you can enable a **reranker**. After the initial search finds a broad set of documents, the reranker uses a powerful cross-encoder model to re-order them based on true contextual relevance. This ensures only the absolute best snippets are sent to the AI.

---

## Setup Guide: Making Your Project RAG-Aware

Follow these steps to configure your project to use the RAG pipeline.

### Prerequisite: Installation

Ensure you have the client-side dependencies installed in your project's virtual environment.

```bash
pip install "my-ai-assistant[client]@git+https://github.com/venoajie/my-ai-assistant.git@develop"
```

### Step 1: Configure the Client (`.ai_config.yml`)

Create a `.ai_config.yml` file in your project's root. This tells the assistant how to find the shared index and which files to use for query expansion.

```yaml
# .ai_config.yml
general:
  # These files power the intelligent query expansion.
  auto_inject_files:
    - "PROJECT_BLUEPRINT.md"
    - "AGENTS.md"

rag:
  # Enable branch-specific indexes (highly recommended for team workflows)
  enable_branch_awareness: true
  
  # Configure the connection to your shared OCI bucket
  oracle_cloud:
    namespace: "your-oci-namespace"
    bucket: "your-oci-bucket-name"
    region: "your-oci-region"

  # --- Optional: Enable and configure the reranker for higher precision results ---
  enable_reranking: true
  retrieval_n_results: 25
  rerank_top_n: 5
```
Commit this file to your repository so the entire team shares the same configuration.

### Step 2: Curate the Knowledge Base (`.aiignore`)
(This section remains the same)

### Step 3: Produce the Index
(This section remains the same)

### Step 4: Usage
(This section remains the same)

---

## Example in Action: The Power of Layered Intelligence

**Scenario:** You want to understand your project's custom error handling. Your codebase contains `utils/error_handling.py` (current) and `utils/legacy_errors.py` (old, deprecated). Your `PROJECT_BLUEPRINT.md` states, "Error handling must use the `CustomAPIException` class."

*   **Before RAG:**
    *   **Prompt:** `ai "How should I handle exceptions?"`
    *   **Result:** A generic, textbook answer about Python's `try...except`. Not project-specific.

*   **With Basic RAG (No Expansion or Reranker):**
    *   **Prompt:** `ai "How should I handle exceptions?"`
    *   **Result:** The RAG plugin finds both `error_handling.py` and `legacy_errors.py`. The AI gets a mixed, confusing context and might suggest using the deprecated legacy class.

*   **With RAG + Query Expansion + Reranker (Recommended):**
    *   **Prompt:** `ai "How should I handle exceptions?"`
    *   **Result:**
        1.  **Expansion:** The system reads `PROJECT_BLUEPRINT.md` and expands your query to something like: *"best practices for exception handling using the CustomAPIException class"*.
        2.  **Retrieval:** This specific query strongly favors `utils/error_handling.py`.
        3.  **Reranking:** The reranker confirms that `utils/error_handling.py` is far more relevant to the expanded query than the legacy file.
    *   **AI Response:** "Based on your project's blueprint, all exceptions should be handled using the `CustomAPIException` class defined in `utils/error_handling.py`..." This answer is clean, precise, and actionable.

## Maintenance and Troubleshooting

### Forcing a Full Re-Index

If you find that RAG is returning poor or stale results, or if you have made significant changes to your `.aiignore` file, your local index may be out of date or incomplete. You can force the system to delete the old index and build a fresh one from scratch.

**Command:**
```bash
# Run this from your project's root directory
# This will delete the existing index and create a new one for the specified branch
ai-index . --force-reindex --branch <your-branch-name>
```
**Example:**
```bash
ai-index . --force-reindex --branch develop
```
This is the best first step for resolving most RAG-related issues.