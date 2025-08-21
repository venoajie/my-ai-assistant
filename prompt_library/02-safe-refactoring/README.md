## Example 2: Safe, Two-Stage Refactoring

This script demonstrates the most important workflow for **modifying files safely**. It uses the two-stage process to generate a plan and then execute it with your approval.

### A Note on AI Reliability
Even with this safe workflow, remember to **always review the generated plan and code**. The `summary.md` and the files in the `workspace/` directory are your chance to catch logical errors or incorrect code before it's ever applied to your project.

### To Run This Example:

1.  **Ensure the dummy file exists:** If you haven't already, run the setup from the `01-basic-analysis` example to create `my_app/utils.py`.
2.  **Make the script executable:** `chmod +x 01-refactor-file.sh`
3.  **Run the script:** `./01-refactor-file.sh`