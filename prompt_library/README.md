# AI Assistant: Hands-On Examples

Welcome to the hands-on examples for the AI Assistant. This guide provides a series of executable scripts that demonstrate the core workflows, from simple analysis to advanced, multi-file orchestration.

## Prerequisites: Setup

Before running any examples, you need to set up your environment.

1.  **Activate Your Virtual Environment:** All commands assume you have an active virtual environment.
    ```bash
    # If you don't have one
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install the AI Assistant:** Install the tool in editable mode with all dependencies for these examples.
    ```bash
    # From the root of the ai-assistant repository
    pip install -e ".[indexing,test]"
    ```

---

## Example 1: Basic Read-Only Analysis

This script demonstrates the safest and most basic workflow: asking an AI specialist to analyze a file without modifying it.

### To Run This Example:

1.  **Create a dummy file:**
    ```bash
    mkdir -p my_app
    cat <<'EOF' > my_app/utils.py
    def calculate_sum(a, b):
        # This function adds two numbers
        result = a + b
        return result

    def get_user_data(user_id):
        # In a real app, this would fetch from a database
        print(f"Fetching data for user {user_id}")
        return {"id": user_id, "name": "Test User"}
    EOF
    ```
2.  **Run the script:**
    ```bash
    ./01-analyze-code.sh
    ```

### The Script: `01-analyze-code.sh`
```bash
#!/bin/bash
set -e

# GOAL: Demonstrate the simplest, safest way to use the AI Assistant
# by asking a specialist persona to review a file and provide feedback.

specialist_persona="core/arc-1"
file_to_review="my_app/utils.py"
query="Please provide a brief architectural review of the attached Python file. Focus on clarity and adherence to best practices."

echo "🚀 Invoking the Architecture Reviewer for a safe, read-only analysis..."

ai --persona "$specialist_persona" \
   -f "$file_to_review" \
   "$query"

echo -e "\n✅ Analysis complete. No files were modified."
```

---

## Example 2: Safe, Two-Stage Refactoring

This script demonstrates the **most important workflow** for modifying files safely. It uses the two-stage process to generate a plan and then execute it only with your explicit approval.

### To Run This Example:

1.  **Ensure the dummy file exists** from Example 1.
2.  **Run the script:**
    ```bash
    ./02-refactor-file.sh
    ```

### The Script: `02-refactor-file.sh`
```bash
#!/bin/bash
set -e

# GOAL: Demonstrate the canonical, safe workflow for modifying a file.

specialist_persona="domains/programming/coder-1"
file_to_modify="my_app/utils.py"
output_dir="ai_runs/refactor_utils_$(date +%Y%m%d-%H%M%S)"
query=$(cat <<'EOF'
<ACTION>
Refactor the attached file `my_app/utils.py`.
Add Python type hints to both functions and include a docstring for the `calculate_sum` function.
</ACTION>
EOF
)

# --- STAGE 1: GENERATE THE PLAN ---
echo "🚀 [STAGE 1/2] Invoking the Software Engineer to generate a refactoring plan..."
echo "   - Output will be saved to: $output_dir"

ai --persona "$specialist_persona" \
   --output-dir "$output_dir" \
   -f "$file_to_modify" \
   "$query"

# --- STAGE 2: REVIEW AND EXECUTE ---
echo -e "\n✅ Plan generated successfully."
echo "   - Review the proposed changes in '$output_dir/summary.md'"
read -p "   - Press Enter to approve and apply the changes..."

echo "🚀 [STAGE 2/2] Executing the plan to apply the changes..."
ai-execute "$output_dir" --confirm

echo -e "\n🎉 Refactoring complete. The file '$file_to_modify' has been updated."
```

---

## Example 3: Using a Project-Local Expert

This example shows how to create and use a custom persona that is an expert on **your specific project's rules**.

### To Run This Example:

1.  **Create the persona file** `.ai/personas/domains/my-app/style-enforcer-1.persona.md` with the content below.
    ```bash
    mkdir -p .ai/personas/domains/my-app
    cat <<'EOF' > .ai/personas/domains/my-app/style-enforcer-1.persona.md
    ---
    alias: domains/my-app/style-enforcer-1
    inherits_from: _base/bcaa-1
    ---
    <SECTION:PRIMARY_DIRECTIVE>
    Your goal is to refactor Python code to meet the specific standards of 'My App', which include adding a standard `logging` import and ensuring all functions have a log entry.
    </SECTION:PRIMARY_DIRECTIVE>
    EOF
    ```
2.  **Run the script:**
    ```bash
    ./03-use-local-expert.sh
    ```

### The Script: `03-use-local-expert.sh`
```bash
#!/bin/bash
set -e

# GOAL: Demonstrate using a custom persona defined in the project.

specialist_persona="domains/my-app/style-enforcer-1"
file_to_modify="my_app/utils.py"
output_dir="ai_runs/style_enforcement_$(date +%Y%m%d-%H%M%S)"
query="<ACTION>Please refactor the attached file to conform to our project's style standards.</ACTION>"

echo "🚀 Invoking our custom 'Style Enforcer' persona..."

ai --persona "$specialist_persona" \
   --output-dir "$output_dir" \
   -f "$file_to_modify" \
   "$query"

echo -e "\n✅ Plan generated. Review the changes in '$output_dir' and then execute:"
echo "   ai-execute \"$output_dir\" --confirm"
```

---

## Example 4: Advanced Orchestration (Batch Processing)

This script demonstrates how to use a shell script as a "conductor" to automate a repetitive task across multiple files. This is the best practice for batch processing.

### To Run This Example:

1.  **Create dummy service files:**
    ```bash
    mkdir -p services/service-alpha services/service-beta
    touch services/service-alpha/main.py
    touch services/service-beta/main.py
    ```
2.  **Run the script:**
    ```bash
    ./04-document-all-services.sh
    ```

### The Script: `04-document-all-services.sh`
```bash
#!/bin/bash
set -e

# GOAL: Demonstrate using a shell script to orchestrate multiple, focused calls to the AI.

specialist_persona="domains/programming/dca-1"
services_to_document=("services/service-alpha" "services/service-beta")

echo "🚀 Starting batch documentation workflow..."

for service_dir in "${services_to_document[@]}"; do
    main_file=$(find "$service_dir" -name "main.py")
    if [ -z "$main_file" ]; then
        echo "   - WARNING: No main.py found in $service_dir. Skipping."
        continue
    fi

    echo "---"
    echo "Processing service: $service_dir"
    output_dir="ai_runs/doc_$(basename "$service_dir")_$(date +%s)"
    query="<ACTION>Create a simple README.md file for the service in the attached file '$main_file'.</ACTION>"
    
    echo "   - [1/2] Generating README plan..."
    ai --persona "$specialist_persona" --output-dir "$output_dir" -f "$main_file" "$query"
       
    echo "   - [2/2] Applying README changes..."
    ai-execute "$output_dir" --confirm
    
    echo "   - ✅ Successfully created README for $service_dir"
done

echo "---"
echo "🎉 Batch documentation workflow complete."
```

---

## Example 5: Codebase-Aware RAG

This example demonstrates the most powerful feature: asking questions about your project without manually attaching files. The RAG system finds the relevant context for you.

### To Run This Example:

1.  **Create a project knowledge base:** We will create a local index of our example files.
    ```bash
    # This command scans the current directory and creates a searchable index.
    ai-index . --branch main
    ```
2.  **Run the query:** Notice we are **not** using the `-f` flag. The AI will find the context automatically.
    ```bash
    ai --persona core/arc-1 "Based on the code in this project, what is the purpose of the 'get_user_data' function?"
    ```

---

## Advanced Tip: On-the-Fly Model Selection

For difficult tasks, you can temporarily override the default models directly from the command line. This is perfect for using a more powerful (but slower) model for a specific, high-stakes task.

```bash
# Use the powerful 'deepseek-reasoner' for planning, but the fast 'gemini-2.5-flash-lite' for synthesis.
ai --persona core/arc-1 \
   --planning-model "deepseek-reasoner" \
   --synthesis-model "gemini-2.5-flash-lite" \
   "Analyze the performance characteristics of the attached code."
```
```