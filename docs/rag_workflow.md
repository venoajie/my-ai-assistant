# Guide: Codebase-Aware Context with RAG

The AI Assistant's Retrieval-Augmented Generation (RAG) pipeline is its most powerful feature for working with large, complex projects. It transforms the assistant from a tool that knows about a few files into an expert that is aware of your entire codebase.

This guide explains the recommended **client-server workflow**, which allows a single powerful machine to manage the knowledge base while the rest of the team uses lightweight clients.

## The Problem RAG Solves

Manually attaching files with the `-f` flag is great for targeted tasks, but it doesn't scale. If you want to ask a broad question like, "How does our authentication system work?" you would need to find and attach every relevant file.

RAG solves this by creating a searchable **knowledge base** of your project. When you ask a question, the assistant first searches this knowledge base to find the most relevant code snippets and documents, then injects them automatically into its context.

---

## The RAG Workflow: A Distributed Model

### Step 1: Set Up the Indexing Environment

One machine on your team should be designated as the "indexer." This machine will build and serve the knowledge base.

1.  **Install with Indexing Dependencies:**
    ```bash
    pip install -e .[indexing]
    ```
2.  **Build the Knowledge Base:** Run the `ai-index` command from your project's root directory.
    ```bash
    ai-index
    ```
    This creates the `.ai_rag_index/` directory containing the vector database. You only need to re-run this command when your codebase changes significantly.

3.  **Serve the Knowledge Base:** Start the ChromaDB server to make the index available to your team.
    ```bash
    # This will serve the index from the specified path on port 8000
    chroma run --host 0.0.0.0 --port 8000 --path .ai_rag_index
    ```

### Step 2: Set Up the Client Environment

All other team members (e.g., on developer laptops) should set up as clients.

1.  **Install the Lightweight Client:**
    ```bash
    pip install -e .[client]
    ```
2.  **Configure the Connection:** In your project's root, create or edit the `.ai_config.yml` file to point to the indexing server.
    ```yaml
    # .ai_config.yml
    rag:
      # Replace with the IP address or hostname of your indexing machine
      chroma_server_host: "192.168.1.100"
      chroma_server_port: 8000
    ```

### Step 3: Use the RAG-Powered Assistant

Now, any time you run an `ai` command from within the project, the assistant will automatically:
1.  Detect the server configuration.
2.  Connect to the remote knowledge base.
3.  Retrieve relevant context for your query.
4.  Inject that context into the prompt for the AI.

```bash
# No special flags needed; the context is injected automatically!
ai --persona domains/programming/csa-1 \
  "Based on the project's codebase, what are the potential performance bottlenecks in the data ingestion pipeline?"
```

### Step 4: Control the Knowledge Base with `.aiignore`

On the **indexing machine**, you can prevent certain files from being included in the knowledge base by creating a `.aiignore` file in the project root.

**Example `.aiignore`:**
```
# .aiignore
# Ignore high-level project management documents
PROJECT_BLUEPRINT.md
# Ignore all project management office artifacts
.ai_pmo/
# Ignore test data
tests/fixtures/
```
After creating or modifying `.aiignore`, rebuild the index on the server machine:
```bash
ai-index --force-reindex
