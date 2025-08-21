## Example 3: Using a Project-Local Expert

This example shows how to create and use a custom persona that is an expert on **your specific project's rules**.

### To Run This Example:

1.  **Create the persona directory:**
    ```bash
    mkdir -p .ai/personas/domains/my-app
    ```
2.  **Create the persona file:** Create the file `.ai/personas/domains/my-app/style-enforcer-1.persona.md` and paste the content below into it.
    ```yaml
    ---
    alias: domains/my-app/style-enforcer-1
    version: 1.0.0
    type: domains
    title: Style Enforcer (My App)
    description: "A specialist that ensures all code in 'My App' follows our strict formatting and logging standards."
    inherits_from: _base/bcaa-1
    ---
    <SECTION:CORE_PHILOSOPHY>
    All code in 'My App' must be clear, documented, and include structured logging for observability.
    </SECTION:CORE_PHILOSOPHY>
    <SECTION:PRIMARY_DIRECTIVE>
    Your goal is to refactor Python code to meet the specific standards of 'My App', which include adding a standard `logging` import and ensuring all functions have a log entry.
    </SECTION:PRIMARY_DIRECTIVE>
    ```
3.  **Make the script executable:** `chmod +x 01-use-local-expert.sh`
4.  **Run the script:** `./01-use-local-expert.sh`