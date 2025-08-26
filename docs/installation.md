# Installation Guide

This guide provides the recommended installation methods for the AI Assistant.

## Core Concept: Tool vs. Project

It is critical to understand that the **AI Assistant is a tool** you install, and **your project is the code you run it on**. The best practice is to install the assistant directly into your project's dedicated virtual environment.

---

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
This command installs the lightweight "client" version of the tool, which is all you need for day-to-day use.

```bash
# Make sure your virtual environment is active!
pip install "git+https://github.com/venoajie/my-ai-assistant.git@develop#egg=my-ai-assistant[client]"
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

Use the `pip install --upgrade` flag with the original Git URL. This tells `pip` to fetch the latest version from the `develop` branch and install it.

```bash
pip install --upgrade "git+https://github.com/venoajie/my-ai-assistant.git@develop#egg=my-ai-assistant[client]"
```

### Step 3: Verify the Update

Check the version of the tool to confirm the update was successful.

```bash
ai --version
