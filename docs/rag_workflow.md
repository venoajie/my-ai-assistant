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
    This is the lightweight phase that happens when you run the `ai` command. The RAG plugin automatically detects your current project and branch, checks for a local copy of the index, and if it's missing or out of date, downloads the latest version from the shared cloud storage. This gives you the power of a full codebase index with the speed of a local database.

---

## Setup Guide: Making Your Project RAG-Aware

Follow these steps to configure your project to use the RAG pipeline.

### Prerequisite: Installation

Ensure you have the client-side dependencies installed in your project's virtual environment. This lightweight installation is all that's needed to connect to a pre-built index.

```bash
# From your project's root, assuming the ai-assistant repo is a sibling directory
pip install -e ../ai-assistant[client]
```

### Step 1: Configure the Client (`.ai_config.yml`)

Create a `.ai_config.yml` file in your project's root. This tells the assistant how to find and connect to the shared index storage.

```yaml
# .ai_config.yml
rag:
  # Enable branch-specific indexes (highly recommended for team workflows)
  enable_branch_awareness: true
  
  # Configure the connection to your shared OCI bucket
  oracle_cloud:
    # The OCI namespace where your bucket resides
    namespace: "your-oci-namespace"
    # The name of the bucket storing the index archives
    bucket: "your-oci-bucket-name"
    # The OCI region for the bucket (e.g., eu-frankfurt-1)
    region: "your-oci-region"
```
Commit this file to your repository so the entire team shares the same configuration.

### Step 2: Curate the Knowledge Base (`.aiignore`)

Create an `.aiignore` file in your project root to control which files are included in the knowledge base. This is critical for excluding secrets, logs, test data, and other irrelevant files to keep the index clean and efficient.

**Example `.aiignore`:**
```
# Standard ignores
.git/
.venv/
__pycache__/
*.log

# Exclude secrets and large data files
/secrets/
/data/
/tests/fixtures/
```
Commit this file to your repository. The CI/CD indexer will respect these rules on its next run.

### Step 3: Produce the Index

You have two options for creating the knowledge base index.

#### Option A: Automated Indexing via CI/CD (Recommended for Teams)

This is the standard, most robust workflow.
1.  Copy the `smart-indexing.yml` GitHub Actions workflow from the AI Assistant project into your own project's `.github/workflows/` directory.
2.  Configure the required `OCI_*` secrets in your repository's GitHub settings.
3.  Push a commit. The action will run automatically, building and uploading the index for your branch.

#### Option B: Manual Local Indexing (For Solo Use or Testing)

You can build the index on your local machine. This is great for getting started quickly or for projects without a CI/CD pipeline.

1.  **Install Indexing Libraries:** This requires the full, heavier dependencies.
    ```bash
    # From your project's environment
    pip install -e ../ai-assistant[indexing]
    ```

2.  **Run the Indexer:** From your project's root, run the `ai-index` command, specifying the branch you want to build an index for.
    ```bash
    # To index your 'main' branch
    ai-index . --branch main
    ```
    This will create the index locally in a `.ai_rag_index` directory. The assistant will find and use this local index.

### Step 4: Usage

That's it! With the configuration in place and an index available (either in OCI or locally), the assistant is now codebase-aware.

Simply run a command as you normally would. The RAG plugin will work automatically in the background to find and inject the most relevant context.

```bash
# The RAG plugin will now automatically find and inject relevant code and docs
ai --persona domains/programming/csa-1 "How does our authentication system work?"
```

---

## Example in Action: Before vs. After RAG

**Scenario:** You want to understand your project's custom error handling.

*   **Before RAG:**
    *   **Prompt:** `ai "How should I handle exceptions in this project?"`
    *   **Result:** A generic, textbook answer about Python's `try...except` blocks. It's correct, but not specific to your project.

*   **With RAG:**
    *   **Prompt:** `ai "How should I handle exceptions in this project?"`
    *   **Result:** The RAG plugin searches the index and finds your `utils/error_handling.py` file, your `logging_config.py`, and a section in your `PROJECT_BLUEPRINT.md` about error standards.
    *   **AI Response:** "Based on your project's existing code, you should use the custom `CustomAPIException` class defined in `utils/error_handling.py`. All exceptions should be caught and logged using the structured logger, which is configured to output JSON format in `logging_config.py`. Your project blueprint also specifies that all 5xx errors must trigger an alert."

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
