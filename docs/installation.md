# Installation Guide

This guide provides the recommended installation methods for the AI Assistant.

## Core Concept: Tool vs. Project

It is critical to understand that the **AI Assistant is a tool** you install, and **your project is the code you run it on**. The best practice is to install the assistant directly into your project's dedicated virtual environment.


## A Critical Note for Teams: Consistent Line Endings

To ensure the RAG "delta" indexing feature works correctly in a team environment (especially with mixed Windows/Linux/macOS developers), you **MUST** create a `.gitattributes` file in the root of your project.

**Why is this mandatory?**
Git can automatically change line endings (LF vs. CRLF). This causes the SHA256 hash of every text file to change, tricking the indexer into thinking every file has been modified. This forces a slow, full re-index on every commit.

**The Fix:** Create a file named `.gitattributes` in your project root with the following content. This enforces consistent line endings for everyone, guaranteeing that delta indexing works as expected.

```
# .gitattributes

# Set default behavior for all files to be text and use LF line endings.
* text=auto eol=lf

# Explicitly declare file types that should always have LF line endings.
*.py eol=lf
*.md eol=lf
*.yml eol=lf
*.yaml eol=lf
*.json eol=lf
*.toml eol=lf
*.sh eol=lf
*.gitignore eol=lf
*.gitattributes eol=lf

# Declare file types that are binary and should not be modified.
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.gz binary

## Method 1: Standard User Installation (Recommended)

This method is for developers who want to use the AI Assistant on their own projects. It installs the tool directly from its Git repository into your current environment.

**Step 1: Activate Your Project's Virtual Environment**
```bash
# Navigate to your project's root directory
cd /path/to/your/trading-app

# Create and activate a virtual environment if you don't have one
python -m venv .venv
source .venv/bin/activate
```

**Step 2: Install the Assistant**
This command uses the modern, PEP 508 compliant syntax to install the lightweight "client" version of the tool. This is all you need to run prompts and connect to a central Librarian RAG service.

```bash
# Make sure your virtual environment is active!
pip install "my-ai-assistant[client]@git+https://github.com/venoajie/my-ai-assistant.git@develop"
```
The `ai`, `ai-execute`, and `ai-index` commands are now available as long as this virtual environment is active.

---

## Method 2: Contributor Installation

This method is for developers who want to contribute to the AI Assistant itself. It requires cloning the repository locally.

**Step 1: Clone the Repository**
```bash
git clone https://github.com/venoajie/my-ai-assistant.git
cd my-ai-assistant
```

**Step 2: Create a Virtual Environment and Install**
```bash
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with all dependencies for testing and development
pip install -e ".[indexing,test]"
```

---

## How to Update the Assistant

To get the latest features, bug fixes, and performance improvements, you should periodically update the tool.

### Step 1: Activate Your Project's Virtual Environment

Ensure you are in the correct environment where the tool was originally installed.

```bash
cd /path/to/your/project
source .venv/bin/activate
```

### Step 2: Run the Upgrade Command

Use the `pip install --upgrade` flag with the modern PEP 508 syntax. This tells `pip` to fetch the latest version from the `develop` branch and install it.

```bash
pip install --upgrade "my-ai-assistant[client]@git+https://github.com/venoajie/my-ai-assistant.git@develop"
```

### Step 3: Verify the Update

Check the version of the tool to confirm the update was successful.

```bash
ai --version
```

## Method 3: Project Bootstrap (Automated Setup)

The fastest way to configure your project is to use the provided `Makefile`. This will interactively prompt you for necessary details and create all the required configuration files for you.

1.  **Copy the Makefile:** Copy the `Makefile` from the AI Assistant repository into the root of your project.
2.  **Run the Setup Command:**

    ```bash
    make ai-setup
    ```

This command will:
*   Ask for your project name and OCI details.
*   Create a `.ai_config.yml` file configured for the RAG workflow.
*   Create a `.aiignore` file to control what gets indexed.
*   Create a `.github/workflows/smart-indexing.yml` file tailored for a project that uses the AI Assistant as a separate tool.
*   Create the `.ai/personas` and `.ai/plugins` directories to encourage best practices.

After running the command, your project is configured. The next step is to provide the CI/CD system with the necessary secrets.