# ai_assistant/prompt_builder.py
from pathlib import Path
from typing import Dict, List, Any

class PromptBuilder:

    def build_planning_prompt(
        self,
        query: str,
        tool_descriptions: str,
        history: List[Dict[str, Any]] = None,
        persona_content: str = None,
        ) -> str:

        history_section = self._build_history_section(history)
        persona_section = ""
        if persona_content:
            persona_section = f"<Persona>\n{persona_content}\n</Persona>\n\n"

        prompt = f"""You are a planning agent. Your SOLE purpose is to convert a user's request into a structured JSON plan of tool calls. You must adhere strictly to the provided tool signatures and planning heuristics. Your primary job is to prepare the complete, final arguments for each tool call.

<AvailableTools>
# You must use the function signatures below to construct your tool calls.
{tool_descriptions}
</AvailableTools>

**PLANNING HEURISTICS (Follow these strictly):**
1.  **Conditional Branching:** To handle uncertainty, create a conditional plan. First, use a listing tool (e.g., `git_list_branches`). Then, create subsequent steps with a `condition` block that checks the output of the first step.
    - Example: `{"tool": "git_create_branch", "args": ..., "condition": {"from_step": 1, "not_in": "my-branch"}}`
2.  **Check Before Creating:** Before creating a resource (like a git branch), your FIRST step must be to use a listing tool (e.g., `git_list_branches`) to check if it already exists.
3.  **Adapt to Context:** Based on the output of the check, your plan should adapt. A robust plan would contain only `git_create_branch` or `git_checkout`, not both.
4.  **Handle Ignored Files:** When asked to `git_add` a file path that is likely to be ignored (e.g., in `logs/`), you MUST use the `force=True` parameter in the `git_add` call.
5.  **CRITICAL: Use Pre-loaded Context for Code Generation:**
    - The user's request may contain one or more `<AttachedFile path="...">` tags with file content. This is your primary source of truth.
    - When the user asks to modify a file (e.g., "refactor this function"), your `write_file` step MUST be fully self-contained.
    - **Step A:** Take the original code from inside the relevant `<AttachedFile>` tag.
    - **Step B:** Perform the requested refactoring or modification on that code.
    - **Step C:** Place the ENTIRE, new, complete file content into the `content` argument of the `write_file` tool.
    - **Step D:** Use the exact file path from the `<AttachedFile path="...">` attribute for the `path` argument.
    - **You are FORBIDDEN from using placeholders, comments like "... rest of file ...", or generating only a diff.** This is not optional. Your job is to generate the complete, final code.
6.  **Summarize, Don't Write:** For read-only tasks (e.g., "summarize", "compare"), if the necessary context is already provided, your plan MUST be an empty array `[]`.

---
<Example>
...
</Example>
---

{history_section}
<UserRequest>
{query}
</UserRequest>

Based on the request, the example, and the heuristics, generate the JSON plan.
You MUST ONLY respond with the JSON plan, enclosed in ```json markdown tags.

JSON_PLAN:
"""
        return prompt
    
    def build_synthesis_prompt(
        self, 
        query: str, 
        history: List[Dict[str, Any]], 
        observations: List[str], 
        persona_content: str = None,
        ) -> str:
        
        history_section = self._build_history_section(history)
        observation_section = "\n".join(observations)
        if persona_content:
            guardrails = f"<SystemPrompt>\n{persona_content}\n</SystemPrompt>"
        else:
            guardrails = self._build_default_guardrails()
            
        failure_protocol = """
**FAILURE HANDLING PROTOCOL:**
If the `<ToolObservations>` section contains errors or indicates that the plan could not be completed:
1.  Your primary objective is to act as a debugger and technical analyst.
2.  Clearly state that the original task could not be completed.
3.  Analyze the error messages in the observations and diagnose the root cause (e.g., "The `git commit` failed due to a missing local user configuration.").
4.  If possible, provide the user with the exact manual commands or steps they need to take to resolve the issue and complete the task.
5.  If you generated any artifacts (like code) before the failure occurred, provide them to the user so their work is not lost.
You MUST provide a helpful, actionable response and are forbidden from returning an empty or null response.
"""
            
        prompt = f"""{guardrails}
You are an expert AI assistant. Your task is to provide a final, comprehensive answer to the user's request based on the preceding conversation and the observations gathered from tool executions.
You MUST embody the persona, philosophy, and directives provided in the SystemPrompt.

{failure_protocol}

{history_section}
<UserRequest>{query}</UserRequest>
<ToolObservations>{observation_section}</ToolObservations>
Synthesize all information to formulate a direct, clear, and actionable response. Adhere strictly to the persona and any specified OUTPUT_CONTRACT. If the plan failed, adhere to the FAILURE HANDLING PROTOCOL.
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
    
    def _build_history_section(
        self, 
        history: List[Dict[str, Any]] = None,
        ) -> str:
        
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
