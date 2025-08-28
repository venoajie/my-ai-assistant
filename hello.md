**File to Modify:** `src/ai_assistant/kernel.py`

**Action:**
1.  Add the following import statement to the top of the file, alongside the other imports:
    ```python
    from .response_handler import ResponseHandler
    ```
2.  Copy the entire `_expand_query_with_context` function below and paste it into the file, just above the `orchestrate_agent_run` function.

```python
```

---

### **Step 2: Integrate the Expansion Logic into the Main Workflow**

Now, we'll modify the `orchestrate_agent_run` function to use our new helper.

**File to Modify:** `src/ai_assistant/kernel.py`

**Action:**
Inside the `orchestrate_agent_run` function, find the line that says `logger.info("Attempting to retrieve RAG context to enhance planning.")`. **Insert the new code block directly above this line**, and then **modify the `rag_plugin.get_context` call** as shown below.

```python
# In src/ai_assistant/kernel.py -> orchestrate_agent_run()

# ... (this code already exists) ...
        except (RecursionError, FileNotFoundError) as e:
            error_msg = f"🛑 HALTING: Could not load persona '{persona_alias}'. Reason: {e}"
            logger.error("Persona loading failed", persona=persona_alias, error=str(e))
            return {"response": error_msg, "metrics": metrics}

# V V V V V PASTE THE NEW CODE BLOCK HERE V V V V V
    # --- END OF NEW SECTION ---

    # --- RAG CONTEXT INJECTION (MODIFIED) ---
# ... (the rest of the function continues as before) ...
```

---

### **Step 3: Configure the Context Files**

Finally, you need to tell the assistant which files to use for context.

**File to Modify:** `.ai_config.yml` (in your project's root directory)

**Action:**
Add the `auto_inject_files` key to the `general` section of your configuration file.

```yaml
# .ai_config.yml

general:
  # We want to store session files in a custom directory for this project.
  sessions_directory: "my_custom_sessions"
  
  # NEW: Specify files that provide high-level project context for query expansion.
  auto_inject_files:
    - "PROJECT_BLUEPRINT.md"
    - "AGENTS.md"

rag:
  enable_branch_awareness: true
  oracle_cloud:
    namespace: frpowqeyehes
    bucket: bucket-20230107-0704
    region: eu-frankfurt-1