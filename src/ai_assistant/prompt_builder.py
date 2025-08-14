# src\ai_assistant\prompt_builder.py
import re
from typing import Dict, List, Any, Optional

class PromptBuilder:
    """
    Constructs prompts for the planning and synthesis stages of the agent.
    This is a stateless utility that combines provided components into a final prompt string.
    """

    def build_planning_prompt(
        self,
        query: str,
        tool_descriptions: str,
        history: List[Dict[str, Any]] = None,
        persona_content: str = None,
        use_compact_protocol: bool = False,
        is_output_mode: bool = False,
        ) -> str:
        """
        Builds the prompt for the Planner, instructing it to create a JSON tool plan.
        """
        history_section = self._build_history_section(history, use_compact_format=use_compact_protocol)
        persona_section = ""
        if persona_content:
            persona_section = f"<Persona>\n{persona_content}\n</Persona>\n\n"

        output_mode_heuristic = ""
        if is_output_mode:
            output_mode_heuristic = """5.  **OUTPUT-FIRST MODE:** You are in a special mode where your plan will NOT be executed directly. Instead, it will be saved to a manifest file. Your plan must be a complete, end-to-end sequence of actions (e.g., create branch, write file, add, commit, push) that can be executed by a separate, non-AI tool. Do not use read-only tools like `list_files` unless their output is critical for a subsequent step's condition. Your primary goal is to generate a complete and executable action plan."""

        prompt = f"""{persona_section}You are a planning agent. Your SOLE purpose is to convert a user's request into a structured JSON plan of tool calls. You must adhere strictly to the provided tool signatures and planning heuristics.

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
{output_mode_heuristic}
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
        persona_context: str,
        directives: Optional[str] = None,
        use_compact_protocol: bool = False
        ) -> str:
        """
        Builds the prompt for the Synthesizer.

        Args:
            query: The original user query.
            history: The preceding conversation history.
            observations: A list of observations from tool executions.
            persona_context: The contextual (non-directive) content of the persona file.
            directives: The pre-parsed <directives> block from the persona, if any.
            use_compact_protocol: Flag to switch to a more compact history format.
        """
        if not persona_context:
            raise ValueError("`persona_context` is a mandatory argument for build_synthesis_prompt.")

        directives_section = directives or ""
        history_section = self._build_history_section(history, use_compact_format=use_compact_protocol)
        observation_section = "\n".join(observations)
        persona_context_section = f"<SystemPrompt>\n{persona_context}\n</SystemPrompt>"

        prompt = f"""{directives_section}
{persona_context_section}
You are an expert AI assistant. Your task is to provide a final, comprehensive answer to the user's request based on the preceding conversation and the observations gathered from tool executions.
You MUST embody the persona, philosophy, and directives provided in the SystemPrompt.

{history_section}
<UserRequest>{query}</UserRequest>
<ToolObservations>{observation_section}</ToolObservations>
Synthesize all information to formulate a direct, clear, and actionable response.
"""
        return prompt

    def _build_history_section(
        self,
        history: List[Dict[str, Any]] = None,
        use_compact_format: bool = False
        ) -> str:
        """
        Builds the conversation history section of the prompt.
        Switches between a verbose XML-like format and a compact format.
        """
        if not history: return ""

        if use_compact_format:
            history_lines = []
            for turn in history:
                role = turn.get('role', 'unknown').upper()
                content = turn.get('content', '')
                if role in ['USER', 'ASSISTANT', 'MODEL']: # 'MODEL' for backward compatibility
                    role_display = 'USER' if role == 'USER' else 'ASSISTANT'
                    history_lines.append(f"[{role_display}]: {content}")
            if not history_lines: return ""
            return "---\nConversation History (compact)\n" + "\n".join(history_lines) + "\n---\n\n"
        else:
            history_section = "<ConversationHistory>\n"
            for turn in history:
                role = turn.get('role', 'unknown')
                content = turn.get('content', '')
                # Basic XML escaping for content
                content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if role == 'user':
                    history_section += f"<UserRequest>{content}</UserRequest>\n"
                elif role in ['assistant', 'model']:
                    history_section += f"<AssistantResponse>{content}</AssistantResponse>\n"
            history_section += "</ConversationHistory>\n\n"
            return history_section
