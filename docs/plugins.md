# Guide: Extending the Assistant with Plugins

Plugins allow you to inject domain-specific knowledge into the AI Assistant, making it "smarter" about your project's unique context. This guide provides a step-by-step tutorial for creating your own custom context plugin.

## What is a Context Plugin?

A context plugin is a simple Python class that analyzes the user's query and attached files to provide extra, relevant information. This information is then added to the context that the AI receives, helping it make better decisions.

For example, a plugin for a trading application could inject definitions of key terms like "order book" or "slippage" whenever it sees those words in a query.

## Step 1: Create the Plugin File

Create a new Python file for your plugin. For this example, we will create a plugin named "DataScience".

**File:** `src/ai_assistant/plugins/datascience_plugin.py`

## Step 2: Define the Plugin Class

In your new file, define a class that inherits from `ContextPluginBase`. It must have a `name` attribute and a `get_context` method.

```python
# src/ai_assistant/plugins/datascience_plugin.py
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

## Step 3: Register the Plugin

The assistant discovers plugins using Python's "entry points" mechanism. You must register your new plugin in the `pyproject.toml` file.

**File:** `pyproject.toml`

Add the following lines under the `[project.entry-points."ai_assistant.context_plugins"]` section:

```toml
[project.entry-points."ai_assistant.context_plugins"]
trading = "ai_assistant.plugins.trading_plugin:TradingContextPlugin"
# Add your new plugin below
datascience = "ai_assistant.plugins.datascience_plugin:DataScienceContextPlugin"
```
The format is `plugin_name = "path.to.module:ClassName"`.

## Step 4: Use the Plugin

After reinstalling the package in editable mode (`pip install -e .`) to register the new entry point, you can use your plugin via the `--context` flag.

```bash
# List available plugins to confirm yours is registered
ai --list-plugins

# Use your new plugin in a prompt
ai --new-session --context DataScience \
  "How can I optimize the ETL process for this large dataframe?"
```

The AI will now receive the extra context you defined, leading to a more informed and accurate response.
```
