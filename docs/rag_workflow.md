
# Guide: Setting Up Codebase-Aware Context (RAG)

The AI Assistant's Retrieval-Augmented Generation (RAG) pipeline is its most powerful feature for working with large, complex projects. It transforms the assistant from a tool that knows about a few manually attached files into an expert that is aware of your **entire codebase**.

This guide will walk you through setting up this modern, scalable workflow for your own project.

## The Problem RAG Solves

Manually attaching files with the `-f` flag is great for targeted tasks, but it doesn't scale. If you want to ask a broad question like, "How does our authentication system work?" you would need to find and attach every relevant file yourself.

RAG solves this by creating a searchable **knowledge base** of your project. When you ask a question, the assistant first queries this knowledge base to find the most relevant code snippets and documents, then automatically injects them into its context before contacting the AI.

---

## How It Works: The Three-Tiered Ecosystem

The RAG pipeline is a distributed system designed for a robust team environment. It consists of three decoupled components:

1.  **The Producer (Automated via CI/CD):**
    This is the "heavy lifting" phase, handled by an automated process like GitHub Actions. On every `git push`, the CI/CD system checks out the code, scans it, and creates a vector database—the "index"—of your project for that specific branch. This index is then packaged and uploaded to a shared cloud object store (like OCI Object Storage).

2.  **The Consumer (The Librarian Service):**
    This is a centralized, long-running API service that you deploy. On startup, it downloads the latest index for a specific branch from the cloud, loads it into memory, and exposes a secure API endpoint for querying it. It is the single source of truth for codebase context.

3.  **The Client (Your `ai` Command):**
    This is the lightweight phase that happens on your machine. When you run the `ai` command, the RAG plugin no longer performs heavy local processing. Instead, it securely connects to the Librarian service, sends your query, and receives the most relevant context snippets. This context is then injected into your prompt.

This architecture ensures that all team members get fast, consistent, and up-to-date context without needing powerful local machines or managing local indexes.

---

## Setup Guide: Making Your Project RAG-Aware

Follow these steps to configure your project to use the RAG pipeline.

### Prerequisite: A Deployed Librarian Service

Before your team can use the RAG workflow, an administrator must deploy an instance of the **Librarian RAG Service**. The service's URL and an API key must be distributed to the team.

### Step 1: Configure the Client (`.ai_config.yml`)

Create or update the `.ai_config.yml` file in your project's root. This tells the `ai` command how to connect to the central Librarian service.

```yaml
# .ai_config.yml

rag:
  # The URL of your deployed Librarian service.
  librarian_url: "http://your-librarian-service-host:8000"

  # The API key for authenticating with the Librarian service.
  # It is HIGHLY recommended to set this via the LIBRARIAN_API_KEY environment variable
  # instead of committing it to the file.
  librarian_api_key: ${LIBRARIAN_API_KEY}

  # --- Optional: Configure the number of results to request ---
  max_results: 5
```
Commit this file to your repository. The API key should be managed securely by each developer as an environment variable.

### Step 2: Curate the Knowledge Base (`.aiignore`)

To ensure the RAG index is clean and relevant, create a `.aiignore` file in your project root. This file works exactly like `.gitignore` and tells the CI/CD **Producer** which files and directories to exclude from the knowledge base.

**Example `.aiignore`:**
```
# .aiignore

# Exclude version control, virtual environments, and caches
.git/
.venv/
__pycache__/

# Exclude build artifacts and local configurations
dist/
build/
*.egg-info/
.vscode/

# Exclude large data files that aren't source code
*.csv
/data/
```

### Step 3: Produce the Index (CI/CD)

This step is automated. Your project's repository should be configured with a CI/CD workflow (like the provided `smart-indexing.yml`) that runs the `ai-index` command on every push. This automatically builds and uploads the fresh index that the Librarian service will consume.

### Step 4: Usage

Once configured, using RAG is automatic and transparent. Simply run any `ai` command from within your project directory. The RAG plugin will activate, connect to the Librarian, fetch context, and add it to your prompt behind the scenes. You don't need any special flags.

**Example:**
```bash
# The RAG plugin will automatically find context related to authentication
# before sending the prompt to the AI.
ai --persona domains/programming/python-developer-1 "Explain the authentication flow in this project."
```
