# Guide: Setting Up Codebase-Aware Context (RAG)

The AI Assistant's Retrieval-Augmented Generation (RAG) pipeline is its most powerful feature for working with large, complex projects. It transforms the assistant from a tool that knows about a few manually attached files into an expert that is aware of your **entire codebase**.

This guide will walk you through setting up this modern, scalable workflow for your own project.

## The Problem RAG Solves

Manually attaching files with the `-f` flag is great for targeted tasks, but it doesn't scale. If you want to ask a broad question like, "How does our authentication system work?" you would need to find and attach every relevant file yourself.

RAG solves this by creating a searchable **knowledge base** of your project. When you ask a question, the assistant first queries this knowledge base to find the most relevant code snippets and documents, then automatically injects them into its context before contacting the AI.

---

## How It Works: The Three-Tiered Ecosystem

The RAG pipeline is a distributed system designed for a robust team environment. It consists of three decoupled components, with a dedicated set of services for **each project**.

1.  **The Producer (Automated via CI/CD):**
    This is the "heavy lifting" phase, handled by an automated process like GitHub Actions in **your project's repository**. On every `git push`, the CI/CD system creates a vector index of your project, tagged with the **project name** and **branch name**. This index is then uploaded to a shared cloud object store.

2.  **The Consumer (A Dedicated Librarian Service):**
    For each project (e.g., `trading-app`), a dedicated, long-running **Librarian API service** is deployed. It is configured to download and serve *only* the index for its specific project and branch. This ensures strict data isolation between projects.

3.  **The Client (Your `ai` Command):**
    This is the lightweight phase on your machine. When you run the `ai` command from within your project directory, it reads your local configuration to find the URL of the correct Librarian service. It then securely connects, sends your query, and receives relevant context snippets **only from your project's knowledge base**.

This architecture ensures that all team members get fast, consistent, and correctly-scoped context for the project they are actively working on.

---

## Setup Guide: Making Your Project RAG-Aware

Follow these steps to configure your project to use its dedicated RAG pipeline.

### Prerequisite: A Deployed Librarian Service for Your Project

Before your team can use the RAG workflow, an administrator must deploy an instance of the **Librarian RAG Service** specifically for your project (e.g., a "Librarian for trading-app"). The service's unique URL and API key must be distributed to the team.

### Step 1: Configure the Client Environment (`.env`)

In your project's root directory, create a `.env` file. This file is for secrets and environment-specific URLs and **must not be committed to Git**.

```bash
# .env (in your project's root, e.g., /path/to/trading-app/.env)

# The URL of the Librarian service DEDICATED to this project.
LIBRARIAN_API_URL="http://librarian-for-trading-app.com:8000"

# The secret API key for THAT specific Librarian instance.
LIBRARIAN_API_KEY="your-secret-key-goes-here"
```

### Step 2: Reference the Environment in `.ai_config.yml`

Now, create or update the `.ai_config.yml` file in your project's root. This file **is committed to Git** and tells the `ai` command *how* to use the secrets from your local `.env` file.

```yaml
# .ai_config.yml

rag:
  # This tells the assistant to get the URL from the LIBRARIAN_API_URL
  # variable in your local .env file.
  librarian_url: ${LIBRARIAN_API_URL}

  # This tells the assistant to get the API key from the LIBRARIAN_API_KEY
  # variable in your local .env file.
  librarian_api_key: ${LIBRARIAN_API_KEY}

  # The number of final context chunks to request from the Librarian.
  max_results: 5
```
This two-file system is a security best practice: the configuration is shared, but the secrets are kept local.

### Step 3: Curate the Knowledge Base (`.aiignore`)

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

### Step 4: Produce the Index (CI/CD)

This step is automated. Your project's repository should be configured with a CI/CD workflow (like the provided `smart-indexing.yml`) that runs the `ai-index` command on every push. This automatically builds and uploads the fresh index that the Librarian service will consume.

### Step 5: Usage

Once configured, using RAG is automatic and transparent. Simply run any `ai` command from within your project directory. The RAG plugin will activate, connect to the Librarian, fetch context, and add it to your prompt behind the scenes. You don't need any special flags.

**Example:**
```bash
# The RAG plugin will automatically find context related to authentication
# before sending the prompt to the AI.
ai --persona domains/programming/python-developer-1 "Explain the authentication flow in this project."
```
