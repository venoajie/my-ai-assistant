# ai_assistant/prompt_builder.py
from pathlib import Path
from typing import Dict, List, Any

class PromptBuilder:
    def build_planning_prompt(self, query: str, tool_descriptions: str, history: List[Dict[str, Any]] = None, persona_content: str = None) -> str:
        """Builds a single, robust prompt for generating a complete JSON plan using a few-shot example."""
        history_section = self._build_history_section(history)
        persona_section = ""
        if persona_content:
            persona_section = f"<Persona>\n{persona_content}\n</Persona>\n\n"

        prompt = f"""You are a planning agent. Your SOLE purpose is to convert a user's request into a structured JSON plan of tool calls. You must adhere strictly to the provided tool signatures and planning heuristics.

<AvailableTools>
# You must use the function signatures below to construct your tool calls.
{tool_descriptions}
</AvailableTools>

**PLANNING HEURISTICS (Follow these strictly):**
1.  **Check Before Creating:** Before creating a resource (like a git branch), your FIRST step must be to use a listing tool (e.g., `git_list_branches`) to check if it already exists.
2.  **Adapt to Context:** Based on the output of the check, your plan must adapt. If a branch exists, use `git_checkout`. If not, use `git_create_branch`.
3.  **Handle Ignored Files:** When asked to `git_add` a file path that is likely to be ignored (e.g., in `logs/`), you MUST use the `force=True` parameter in the `git_add` call.
4.  **Recognize Pre-loaded Context:** If the user's request contains one or more `<AttachedFile>` tags, the content of those files is already provided. DO NOT use the `read_file` tool for those files.
5.  **Summarize, Don't Write:** For read-only tasks (e.g., "summarize", "compare", "explain"), if the necessary context is already provided in `<AttachedFile>` tags, your plan MUST be an empty array `[]`. Do not use `write_file` to save the result unless the user explicitly asks for a file to be created.

---
<Example>
<UserRequest>
I need to read the project's README.md file.
</UserRequest>
<JSON_PLAN>
```json
[
  {{
    "thought": "The user wants to read a single file. I will create a one-step plan.",
    "tool_name": "read_file",
    "args": {{
      "path": "README.md"
    }}
  }}
]
```
</JSON_PLAN>
</Example>
---

{history_section}
<UserRequest>
{query}
</UserRequest>

Based on the request, the example, and the heuristics, generate the JSON plan.
You MUST ONLY respond with the JSON plan, enclosed in ```json markdown tags.
Important: Always use a JSON ARRAY of steps, even for single-step plans.

JSON_PLAN:
"""
        return prompt

    def build_synthesis_prompt(self, query: str, history: List[Dict[str, Any]], observations: List[str], persona_content: str = None) -> str:
        history_section = self._build_history_section(history)
        observation_section = "\n".join(observations)
        if persona_content:
            guardrails = f"<SystemPrompt>\n{persona_content}\n</SystemPrompt>"
        else:
            guardrails = self._build_default_guardrails()
        prompt = f"""{guardrails}
You are an expert AI assistant. Your task is to provide a final, comprehensive answer to the user's request based on the preceding conversation and the observations gathered from tool executions.
You MUST embody the persona, philosophy, and directives provided in the SystemPrompt.
{history_section}
<UserRequest>{query}</UserRequest>
<ToolObservations>{observation_section}</ToolObservations>
Synthesize all information to formulate a direct, clear, and actionable response. Adhere strictly to the persona and any specified OUTPUT_CONTRACT.
"""
        return prompt

    def _build_default_guardrails(self) -> str:
        return """<SystemPrompt version="1.0">
<PersonaStandards>
    <CommunicationDirectives>
        - Be clear, direct, and helpful.
        - Structure responses for readability.
    </CommunicationDirectives>
    <StructuredOutput>
        When generating code, place it in a markdown block with the language specified.
    </StructuredOutput>
</PersonaStandards>
</SystemPrompt>"""
    
    def _build_history_section(self, history: List[Dict[str, Any]] = None) -> str:
        if not history: return ""
        history_section = "<ConversationHistory>\n"
        for turn in history:
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')
            content = content.replace('<', '&lt;').replace('>', '&gt;')
            if role == 'user':
                history_section += f"<UserRequest>{content}</UserRequest>\n"
            elif role == 'model':
                history_section += f"<AssistantResponse>{content}</AssistantResponse>\n"
        history_section += "</ConversationHistory>\n\n"
        return history_section
