# Guide: Codebase-Aware Context with RAG

The AI Assistant's Retrieval-Augmented Generation (RAG) pipeline is its most powerful feature for working with large, complex projects. It transforms the assistant from a tool that knows about a few files into an expert that is aware of your entire codebase.

## The Problem RAG Solves

Manually attaching files with the `-f` flag is great for targeted tasks, but it doesn't scale. If you want to ask a broad question like, "How does our authentication system work?" you would need to find and attach every relevant file.

RAG solves this by creating a searchable **knowledge base** of your project. When you ask a question, the assistant first searches this knowledge base to find the most relevant code snippets and documents, then injects them automatically into its context.

---

## The RAG Workflow

Using RAG is a simple, three-step process.

### Step 1: Build Your Knowledge Base

First, you need to tell the assistant to scan your project and build its knowledge base. This is done with the `ai-index` command.

```bash
# Run this from your project's root directory
ai-index
```
This command will:
1.  Scan all non-ignored files in your project.
2.  Split them into small, meaningful chunks.
3.  Convert those chunks into vector embeddings.
4.  Store the embeddings in a local vector database in the `.ai_rag_index/` directory.

You only need to run `ai-index` again when you've made significant changes to your codebase. It's smart enough to only re-index files that have been modified.

### Step 2: Activate RAG Context

To use the knowledge base, simply add the `--context rag` flag to your prompt.

```bash
ai --context rag --persona domains/programming/csa-1 \
  "Based on the project's codebase, what are the potential performance bottlenecks in the data ingestion pipeline?"
```
Instead of you finding the files, the RAG plugin will search the index for chunks related to "performance bottlenecks" and "ingestion pipeline" and provide them to the AI.

### Step 3: Control the Knowledge Base with `.aiignore`

Sometimes you want to prevent certain files or directories from being included in the knowledge base. For example, you might want to exclude high-level project management documents, test fixtures, or build artifacts.

You can do this by creating a `.aiignore` file in your project root. It works just like a `.gitignore` file.

**Example `.aiignore`:**
```
# .aiignore

# Ignore high-level project management documents
PROJECT_BLUEPRINT.md
PROJECT_ROADMAP.md

# Ignore all project management office artifacts
.ai_pmo/

# Ignore test data
tests/fixtures/
```
After creating or modifying your `.aiignore` file, you should rebuild the index to ensure the changes take effect:
```bash
ai-index --force-reindex
```

This workflow gives you complete control over the AI's knowledge, allowing you to create a highly-focused, project-aware expert.
