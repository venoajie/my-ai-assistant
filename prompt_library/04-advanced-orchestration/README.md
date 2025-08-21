## Example 4: Advanced Orchestration

This script demonstrates how to use a shell script to automate a repetitive task across multiple files. This is the best practice for batch processing.

### To Run This Example:

1.  **Create dummy service files:**
    ```bash
    mkdir -p services/service-alpha services/service-beta
    touch services/service-alpha/main.py
    touch services/service-beta/main.py
    ```
2.  **Make the script executable:** `chmod +x 01-document-all-services.sh`
3.  **Run the script:** `./01-document-all-services.sh`