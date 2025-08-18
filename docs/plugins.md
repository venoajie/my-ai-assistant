# Guide: Extending the Assistant with Plugins

Plugins allow you to inject domain-specific knowledge into the AI Assistant, making it "smarter" about your project's unique context. This guide provides a step-by-step tutorial for creating your own custom context plugin, covering both built-in and local plugins, and the concept of automatic domain-based loading.

## Hybrid Model of Built-in and Local Plugins

The AI Assistant supports a hybrid model of plugins:
- **Built-in Plugins:** These are plugins that are included with the AI Assistant and are available to all projects. They are registered via entry points in the `pyproject.toml` file.
- **Local Plugins:** These are project-specific plugins that are stored in the `.ai/plugins/` directory within your project. They are automatically discovered and loaded by the AI Assistant.

## Automatic Domain-Based Loading

When a persona from a specific domain is selected (e.g., `domains/DataScience`), the AI Assistant attempts to auto-load a context plugin associated with that domain. The plugin name is derived from the domain name (e.g., `domains-DataScience`).

## Tutorial: Creating a Local Plugin

### Step 1: Create the Plugin File

Create a new Python file for your plugin in the `.ai/plugins/` directory. For this example, we will create a plugin named "DataScience".

**File:** `.ai/plugins/datascience_plugin.py`

### Step 2: Define the Plugin Class

In your new file, define a class that inherits from `ContextPluginBase`. It must have a `name` attribute and a `get_context` method.

```python
# .ai/plugins/datascience_plugin.py
from typing import List
from pathlib import Path
from ai_assistant.context_plugin import ContextPluginBase

class DataScienceContextPlugin(ContextPluginBase):
    """
    Provides context for data science projects, especially those using pandas.
    """
    name = "DataScience"
    
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def get_context(self, query: str, files: List[str]) -> str:
        """
        If the query mentions 'dataframe' or 'etl', inject knowledge
        about common pandas operations.
        """
        context_str = ""
        query_lower = query.lower()
        
        if "dataframe" in query_lower or "etl" in query_lower:
            context_str += "<DataScienceKnowledge>\n"
            context_str += "  - A pandas DataFrame is an in-memory, two-dimensional, labeled data structure.\n"
            context_str += "  - Common ETL (Extract, Transform, Load) operations include merging, grouping, and cleaning data.\n"
            context_str += "  - For performance, prefer vectorized operations over row-by-row iteration.\n"
            context_str += "</DataScienceKnowledge>\n"
        
        return context_str
```

### Step 3: Use the Plugin

After creating your plugin, you can use it in your project. The AI Assistant will automatically discover and load plugins from the `.ai/plugins/` directory.

```bash
# List available plugins to confirm yours is registered
ai --list-plugins

# Use your new plugin in a prompt
ai --new-session --context DataScience \
  "How can I optimize the ETL process for this large dataframe?"
```

The AI will now receive the extra context you defined, leading to a more informed and accurate response.