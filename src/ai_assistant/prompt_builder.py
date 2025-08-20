# src\ai_assistant\prompt_builder.py
from typing import Dict, List, Any, Optional
import json
from .data_models import ExecutionPlan

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

        # --- THIS PROMPT IS NOW MUCH SIMPLER ---
        prompt = f"""{persona_section}You are a planning agent. Your SOLE purpose is to convert a user's request into a structured plan of tool calls. Adhere strictly to the provided tool signatures and planning heuristics.

<AvailableTools>
# You must use the function signatures below to construct your tool calls.
{tool_descriptions}
</AvailableTools>

**PLANNING HEURISTICS (Follow these strictly):**
1.  **Conditional Branching:** For uncertainty, use a read-only tool first, then use a `condition` block on subsequent steps that references the first step's output.
2.  **Handle Ignored Files:** When using `git_add` on a potentially ignored file, use the `force=True` parameter.
3.  **CRITICAL: Use Pre-loaded Context for Code Generation:** When modifying a file provided in an `<AttachedFile>` tag, your `write_file` step MUST contain the ENTIRE, new, complete file content. Do not use placeholders.
4.  **Summarize, Don't Read:** If context is already in `<AttachedFile>`, generate an empty plan `[]` for summarization tasks. Do not use `read_file` on an already attached file.
{output_mode_heuristic}
---
{history_section}
<UserRequest>
{query}
</UserRequest>

Based on the request and heuristics, generate the plan.
"""
        return prompt


    def build_critique_prompt(
        self,
        query: str,
        plan: ExecutionPlan,
        persona_context: str
    ) -> str:
        """Builds the prompt for the Plan Validation Analyst."""

        plan_dict = plan.model_dump() 
        plan_str = json.dumps(plan_dict, indent=2)     
           
        prompt = f"""<SystemPrompt>
{persona_context}
</SystemPrompt>

You are a skeptical "red team" analyst. Your sole purpose is to find flaws in a proposed plan.

A user has made the following request:
<UserRequest>
{query}
</UserRequest>

An AI planner has generated the following execution plan to satisfy the request:
<JSON_PLAN>
```json
{plan_str}
```
</JSON_PLAN>

Critically evaluate this plan based on your operational protocol. Identify unstated assumptions, dangerous edge cases, security risks, or logical errors. Provide a concise, bulleted list of your findings. If the plan is sound, state that clearly.
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