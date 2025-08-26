# src/ai_assistant/prompt_builder.py
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
        plan_expectation: Optional[Dict[str, Any]] = None, 
        ) -> str:
        """

        Builds the prompt for the Planner, instructing it to create a JSON tool plan.
        """
        history_section = self._build_history_section(
            history,
            use_compact_format=use_compact_protocol,
            )
        persona_section = ""
        if persona_content:
            persona_section = f"<PersonaInstructions>\n{persona_content}\n</PersonaInstructions>\n\n"

        # --- Dynamically build the compliance section ---
        compliance_section = ""
        if plan_expectation:
            allowed_tools_str = ", ".join(f"'{t}'" for t in plan_expectation.get('allowed_tools', []))
            max_steps = plan_expectation.get('max_steps')
            rules = []
            if allowed_tools_str:
                rules.append(f"- The plan MUST exclusively use tools from this list: [{allowed_tools_str}].")
            if max_steps is not None:
                rules.append(f"- The plan MUST NOT exceed {max_steps} step(s).")
            
            if rules:
                rules_str = "\n".join(rules)
                compliance_section = f"""
<ComplianceRequirements>
CRITICAL: Based on an automated analysis of the user's request, you MUST adhere to the following strict rules when generating the plan. Failure to comply will result in immediate rejection.
{rules_str}
</ComplianceRequirements>
"""

        output_mode_heuristic = ""
        if is_output_mode:
            output_mode_heuristic = """5.  **OUTPUT-FIRST MODE:** You are in a special mode where your plan will NOT be executed directly. Instead, it will be saved to a manifest file. Your plan must be a complete, end-to-end sequence of actions (e.g., create branch, write file, add, commit, push) that can be executed by a separate, non-AI tool. Do not use read-only tools like `list_files` unless their output is critical for a subsequent step's condition. Your primary goal is to generate a complete and executable action plan."""

        prompt = f"""{persona_section}
<Task>
You are a planning agent. Your SOLE purpose is to convert a user's request into a structured plan of tool calls. Adhere strictly to the provided tool signatures and planning heuristics.
</Task>

{compliance_section} 

<AvailableTools>
# You must use the function signatures below to construct your tool calls.
{tool_descriptions}
</AvailableTools>

<PlanningHeuristics>
1.  **Conditional Branching:** For uncertainty, use a read-only tool first, then use a `condition` block on subsequent steps that references the first step's output.
2.  **Handle Ignored Files:** When using `git_add` on a potentially ignored file, use the `force=True` parameter.
3.  **CRITICAL: Use Pre-loaded Context for Code Generation:** When modifying a file provided in an `<AttachedFile>` tag, your `write_file` step MUST contain the ENTIRE, new, complete file content. Do not use placeholders.
4.  **Answer from Context:** If the user's question can be fully answered by information already present in the conversation history or attached context (like RAG results), your goal is to signal that no tools are needed. To do this, generate an empty plan: `[]`. Do not use tools to re-process information you already have.
{output_mode_heuristic}
</PlanningHeuristics>

{history_section}

<FinalUserRequest>
{query}
</FinalUserRequest>

Based on the final user request and all provided context, generate the plan.
"""
        return prompt


    def build_critique_prompt(
        self,
        query: str,
        plan: ExecutionPlan,
        persona_context: str,
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
        use_compact_protocol: bool = False,
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
        history_section = self._build_history_section(
            history, 
            use_compact_format=use_compact_protocol,
            )
        observation_section = "\n".join(observations)
        persona_context_section = f"<SystemPrompt>\n{persona_context}\n</SystemPrompt>"

        prompt = f"""{directives_section}
{persona_context_section}
You are an expert AI assistant. Your task is to provide a final, comprehensive answer to the user's request based on the preceding conversation and the observations gathered from tool executions.
You MUST embody the persona, philosophy, and directives provided in the SystemPrompt.

{history_section}
<UserRequest>{query}</UserRequest>
<ToolObservations>{observation_section}</ToolObservations>

<AnsweringProtocol>
CRITICAL: The information provided in `<ToolObservations>` is your SOLE SOURCE OF TRUTH. Your primary task is to synthesize an answer based *exclusively* on this data. If the observations contain code, explain that specific code. Do not use your general knowledge about other topics or libraries, even if the user's query seems generic. If the observations are empty, state that you have no information.
</AnsweringProtocol>

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