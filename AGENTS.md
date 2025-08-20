# AGENTS.md: Operator's Manual for AI Assistant

## 1. System Requirements
- **Python Version:** Python 3.10 or higher is **required**.
- **Reason:** The project relies on modern dependencies (e.g., `instructor`) that use typing syntax (`|` for unions) introduced in Python 3.10. It will not run on older versions.

## 2. Core Commands
- **Install Dependencies:** `pip install -e .[test]`
- **Run Tests:** `pip install -e .[test] && python -m unittest`
- **Run Application:** `ai` or `ai-execute`