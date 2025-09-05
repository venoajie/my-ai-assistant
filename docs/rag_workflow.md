# Guide: Setting Up Codebase-Aware Context (RAG)

The AI Assistant's Retrieval-Augmented Generation (RAG) pipeline is its most powerful feature for working with large, complex projects. It transforms the assistant from a tool that knows about a few manually attached files into an expert that is aware of your **entire codebase**.

This guide will walk you through setting up this modern, scalable workflow for your own project.

## The Problem RAG Solves

Manually attaching files with the `-f` flag is great for targeted tasks, but it doesn't scale. If you want to ask a broad question like, "How does our authentication system work?" you would need to find and attach every relevant file yourself.

RAG solves this by creating a searchable **knowledge base** of your project in a central database. When you ask a question, the assistant queries this knowledge base to find the most relevant code snippets, which are then automatically injected into its context.

---

## How It Works: The Three-Tiered Ecosystem

The RAG pipeline is a distributed system designed for a robust team environment. It consists of three decoupled components that work together to serve multiple projects from a single, centralized infrastructure.

1.  **The Producer (Automated via CI/CD in Your Project):**
    This is the "heavy lifting" phase, handled by an automated process (GitHub Actions) in **your project's repository**. On every `git push`, the CI/CD system runs the `ai-index` command. This command connects to a **central PostgreSQL database**, populates a table unique to your project and branch, and uploads a small "manifest" file to a shared cloud object store.

2.  **The Consumer (The Central Librarian Service):**
    A single, central, long-running **Librarian API service** is deployed for the entire organization. It is a multi-tenant service. When it receives a request, it's told which project the request is for. It then fetches the correct manifest from the cloud to identify the right table in the database and performs the query.

3.  **The Client (Your `ai` Command):**
    This is the lightweight phase on your machine. When you run the `ai` command, it reads your local configuration to find the URL of the central Librarian service. It then securely connects, sends your query, and receives relevant context snippets **only from your project's knowledge base**.

This architecture allows multiple teams and projects to share a single, powerful RAG infrastructure while maintaining perfect data isolation.

---

## Setup Guide: Making Your Project RAG-Aware

Follow these steps to configure your project to use the central RAG pipeline.

### Prerequisite: A Deployed Central Librarian Service

Your organization must have a deployed instance of the **Librarian RAG Service**. Its URL and a shared API key must be distributed to all teams.

### Step 1: Configure the Client Environment (`.env`)

In your project's root directory, create a `.env` file. This file is for secrets and **must not be committed to Git**.

```bash
# .env (in your project's root, e.g., /path/to/your-project/.env)

# The URL of the CENTRAL Librarian service.
LIBRARIAN_API_URL="http://central-librarian.my-company.com:8000"

# The secret API key for the Librarian service.
LIBRARIAN_API_KEY="your-secret-key-goes-here"
```

### Step 2: Reference the Environment in `.ai_config.yml`

Create or update the `.ai_config.yml` file in your project's root. This file **is committed to Git** and tells the `ai` command *how* to use the secrets from your local `.env` file.

```yaml
# .ai_config.yml

rag:
  # This tells the assistant to get the URL from the LIBRARIAN_API_URL
  # variable in your local .env file.
  librarian_url: ${LIBRARIAN_API_URL}

  # This tells the assistant to get the API key from the LIBRARIAN_API_KEY
  # variable in your local .env file.
  librarian_api_key: ${LIBRARIAN_API_KEY}
```

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

This step is automated. Your project's repository must be configured with a CI/CD workflow (like the provided `smart-indexing.yml`) that runs the `ai-index` command on every push. This automatically builds and populates the central database with a fresh index for your project. For details on setting this up, see the main `README.md`.

### Step 5: Usage

Once configured, using RAG is automatic and transparent. Simply run any `ai` command from within your project directory. The RAG plugin will activate, connect to the Librarian, fetch context, and add it to your prompt behind the scenes. You don't need any special flags.

**Example:**
```bash
# The RAG plugin will automatically find context related to authentication
# before sending the prompt to the AI.
ai --persona domains/programming/python-developer-1 "Explain the authentication flow in this project."
```
