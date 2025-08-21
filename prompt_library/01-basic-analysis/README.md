## Example 1: Basic Read-Only Analysis

This script demonstrates the safest and most basic workflow: asking an AI specialist to analyze a file without modifying it.

### To Run This Example:

1.  **Create a dummy file:** Create a file named `my_app/utils.py` with some simple Python code in it.
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
2.  **Make the script executable:** `chmod +x 01-analyze-code.sh`
3.  **Run the script:** `./01-analyze-code.sh`