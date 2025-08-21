# Guide: Extending the Assistant with Plugins

Plugins are the primary mechanism for injecting deep, domain-specific knowledge into the AI Assistant, making it "smarter" about your project's unique context, business logic, and technical conventions.

While personas define an agent's *role and process*, plugins provide the underlying *knowledge base* they work from.

## Why Create a Plugin?

Imagine your project has a complex internal library with specific rules. Instead of explaining these rules in every prompt, you can encode them into a plugin. The plugin will automatically inject this knowledge whenever a relevant keyword is mentioned.

This guide focuses on **Local Plugins**, which are the best practice for project-specific work.

## Tutorial: Creating a Local Plugin

Let's create a plugin that teaches the assistant about your project's custom data science library.

### Step 1: Create the Plugin File

In your project root, create a new Python file in the `.ai/plugins/` directory. The filename must end with `_plugin.py`.

**File:** `.ai/plugins/datascience_plugin.py`

### Step 2: Define the Plugin Class

In your new file, define a class that inherits from `ContextPluginBase`. It must have a `name` attribute and a `get_context` method.

```python
# .ai/plugins/datascience_plugin.py
from typing import List, Dict
from pathlib import Path
from ai_assistant.context_plugin import ContextPluginBase

class DataScienceContextPlugin(ContextPluginBase):
    """
    Provides context for our project's data science conventions.
    """
    name = "DataScience"
    
    def get_context(self, query: str, files: List[str]) -> str:
        """
        If the query mentions 'dataframe' or 'etl', inject knowledge
        about our internal library and best practices.
        """
        context_str = ""
        query_lower = query.lower()
        
        if "dataframe" in query_lower or "etl" in query_lower:
            context_str += "<ProjectKnowledge source='DataSciencePlugin'>\n"
            context_str += "  - CRITICAL: Always use the `project_lib.etl.load_dataframe()` function, as it handles authentication automatically.\n"
            context_str += "  - For performance, prefer vectorized operations over row-by-row iteration.\n"
            context_str += "  - All final dataframes must be validated with `project_lib.validation.validate_schema()` before being saved.\n"
            context_str += "</ProjectKnowledge>\n"
        
        return context_str
```

### Step 3: Use the Plugin

The AI Assistant automatically discovers local plugins. You can confirm it's loaded by listing all available plugins.

```bash
# The output will include "datascience (local)"
ai --list-plugins

# Now, use your plugin in a prompt with the --context flag
# Note: The name is derived from the filename (datascience_plugin.py -> datascience)
ai --context 'datascience (local)' \
  "How should I load this CSV into a dataframe for our ETL process?"
```

The AI will now receive the critical, project-specific context you defined, guiding it to generate a correct and compliant answer that uses your internal library.

> **Pro Tip:** Manually loading your plugin with `--context` is great for testing, but the real power comes from automation. Learn how to make the assistant automatically load your plugin and other key files in the **[Project-Specific Configuration Guide](./project_configuration.md)**.
