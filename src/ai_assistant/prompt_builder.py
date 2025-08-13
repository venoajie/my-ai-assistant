# src/ai_assistant/prompt_builder.py
from pathlib import Path
from typing import Dict, List, Any

# --- REFACTOR: Define two versions of the failure protocol as per approved proposal ---
# This is the high-fidelity, verbose version used for standard requests to ensure maximum clarity.
_FAILURE_PROTOCOL_VERBOSE = """<META_DIRECTIVE>
**CRITICAL: FAILURE HANDLING PROTOCOL**
Your behavior is dictated by this primary rule: If ANY tool observation in the `<ToolObservations>` section contains the words 'Error', 'Failure', or 'CRITICAL FAILURE', you MUST immediately abandon your primary persona and adopt the role of a **Debugging Analyst**.

As a Debugging Analyst, your response MUST follow this structure:
1.  **State Failure:** Begin by clearly stating that the original task could not be completed.
2.  **Root Cause Analysis:** Analyze the error messages in the observations and provide a concise diagnosis of the root cause.
3.  **Recovery Plan:** Provide the user with the exact, numbered, manual commands or steps they need to take to resolve the issue and complete the task.
4.  **Provide Artifacts:** If any artifacts (like code) were successfully generated before the failure, present them to the user in a "Generated Artifacts" section so their work is not lost.

This protocol OVERRIDES all other persona directives. You are FORBIDDEN from returning an empty response if a failure is present.
</META_DIRECTIVE>
"""

# This is the token-efficient, compact version used only when the context size is very large.
_FAILURE_PROTOCOL_COMPACT = """<MetaDirective>
**FAILURE PROTOCOL** (OVERRIDES ALL): If observations contain 'Error'/'Failure', you are a Debugging Analyst.
1. State failure.
2. Analyze root cause from observations.
3. Provide numbered, manual recovery steps for the user.
4. Present any generated artifacts.
This protocol is mandatory.
</MetaDirective>"""


class PromptBuilder:
    """
    Constructs prompts for the planning and synthesis stages of the agent.
    """

    def build_planning_prompt(
        self,
        query: str,
        tool_descriptions: str,
        history: List[Dict[str, Any]] = None,
        persona_content: str = None,
        ) -> str:
        """
        Builds the prompt for the Planner, instructing it to create a JSON tool plan.
        This prompt remains unchanged by the recent optimizations as its verbosity is
        critical for reliable planning.
        """
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
1.  **Conditional Branching for Uncertainty:** To handle situations with unknown state (e.g., whether a file or branch exists), you MUST create a conditional plan.
    - **Step A:** The first step should be a read-only tool to check the state (e.g., `git_list_branches`).
    - **Step B:** Subsequent steps that depend on this state MUST include a `condition` block that references the output of the first step.
    - **Example:** `{{"tool": "git_create_branch", "args": ..., "condition": {{"from_step": 1, "not_in": "my-branch"}}}}`
2.  **Handle Ignored Files:** When asked to `git_add` a file path that is likely to be ignored (e.g., in `logs/`), you MUST use the `force=True` parameter in the `git_add` call.
3.  **CRITICAL: Use Pre-loaded Context for Code Generation:**
    - The user's request may contain one or more `<AttachedFile path="...">` tags with file content. This is your primary source of truth.
    - When the user asks to modify a file (e.g., "refactor this function"), your `write_file` step MUST be fully self-contained.
    - **Step A:** Take the original code from inside the relevant `<AttachedFile>` tag.
    - **Step B:** Perform the requested refactoring or modification on that code.
    - **Step C:** Place the ENTIRE, new, complete file content into the `content` argument of the `write_file` tool.
    - **Step D:** Use the exact file path from the `<AttachedFile path="...">` attribute for the `path` argument.
    - **You are FORBIDDEN from using placeholders, comments like "... rest of file ...", or generating only a diff.** This is not optional. Your job is to generate the complete, final code.
4.  **Summarize, Don't Write:** For read-only tasks (e.g., "summarize", "compare"), if the necessary context is already provided, your plan MUST be an empty array `[]`.

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


    def build_synthesis_prompt(
        self,
        query: str,
        history: List[Dict[str, Any]],
        observations: List[str],
        persona_content: str = None,
        use_compact_protocol: bool = False # --- REFACTOR: Added flag for conditional compression ---
        ) -> str:
        """
        Builds the prompt for the Synthesizer, which formulates the final response.
        It conditionally uses compact formats to save tokens on large inputs.
        """
        # --- REFACTOR: Use compact history format and select protocol based on the flag ---
        history_section = self._build_history_section(history, use_compact_format=use_compact_protocol)
        observation_section = "\n".join(observations)
        if persona_content:
            guardrails = f"<SystemPrompt>\n{persona_content}\n</SystemPrompt>"
        else:
            guardrails = self._build_default_guardrails()

        # Select the appropriate failure protocol based on context size
        failure_protocol = _FAILURE_PROTOCOL_COMPACT if use_compact_protocol else _FAILURE_PROTOCOL_VERBOSE

        prompt = f"""{failure_protocol}
{guardrails}
You are an expert AI assistant. Your task is to provide a final, comprehensive answer to the user's request based on the preceding conversation and the observations gathered from tool executions.
You MUST embody the persona, philosophy, and directives provided in the SystemPrompt, but you MUST adhere to the FAILURE HANDLING PROTOCOL meta-directive above all else.

{history_section}
<UserRequest>{query}</UserRequest>
<ToolObservations>{observation_section}</ToolObservations>
Synthesize all information to formulate a direct, clear, and actionable response.
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
        use_compact_format: bool = False # --- REFACTOR: Added flag for format switching ---
        ) -> str:
        """
        Builds the conversation history section of the prompt.
        Switches between a verbose XML-like format and a compact format.
        """
        if not history: return ""

        # --- REFACTOR: Switch between verbose and compact history formats ---
        if use_compact_format:
            history_lines = []
            for turn in history:
                role = turn.get('role', 'unknown').upper()
                content = turn.get('content', '')
                if role in ['USER', 'MODEL']:
                    # Use a simple, token-efficient format
                    history_lines.append(f"[{role}]: {content}")
            if not history_lines: return ""
            return "---\nConversation History (compact)\n" + "\n".join(history_lines) + "\n---\n\n"
        else:
            # Original verbose format for maximum clarity
            history_section = "<ConversationHistory>\n"
            for turn in history:
                role = turn.get('role', 'unknown')
                content = turn.get('content', '')
                # Basic XML escaping for safety
                content = content.replace('<', '&lt;').replace('>', '&gt;')
                if role == 'user':
                    history_section += f"<UserRequest>{content}</UserRequest>\n"
                elif role == 'model':
                    history_section += f"<AssistantResponse>{content}</AssistantResponse>\n"
            history_section += "</ConversationHistory>\n\n"
            return history_section