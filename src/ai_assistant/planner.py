# src/ai_assistant/planner.py
import json
import re
from typing import List, Dict, Any, Optional, Tuple

from .prompt_builder import PromptBuilder
from .response_handler import ResponseHandler
from .tools import TOOL_REGISTRY
from .config import ai_settings

class Planner:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.response_handler = ResponseHandler()

    async def create_plan(
        self, 
        query: str, 
        history: List[Dict[str, Any]] = None, 
        persona_content: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], float]:
        print("🤔 Generating execution plan...")
        tool_descriptions = TOOL_REGISTRY.get_tool_descriptions()
        prompt = self.prompt_builder.build_planning_prompt(
            query, 
            tool_descriptions, 
            history, 
            persona_content,
            )

        planning_model = ai_settings.model_selection.planning
        planning_generation_config = ai_settings.generation_params.planning.model_dump()

        if "deepseek" in planning_model:
            planning_generation_config["response_format"] = {"type": "json_object"}

        api_result = await self.response_handler.call_api(
            prompt,
            model=planning_model,
            generation_config=planning_generation_config
        )

        response_text = api_result["content"]
        planning_duration = api_result["duration"]

        plan = self._extract_and_validate_plan(response_text)

        if not plan:
            if isinstance(plan, list):
                print("✅ Plan generated successfully (No tool execution required).")
            # --- Return duration even for no-op plans ---
            return plan, planning_duration
                    
        print("✅ Plan generated successfully.")
        for i, step in enumerate(plan):
            print(f"  - Step {i+1}: {step.get('thought', '')} -> {step.get('tool_name')}({step.get('args', {})})")
        return  plan, planning_duration
        
    def _extract_and_validate_plan(self, response_text: str) -> List[Dict[str, Any]]:
        """Extracts, sanitizes, repairs, and validates a JSON plan from raw LLM text."""
        
        # This function remains synchronous as it performs CPU-bound string operations.
        response_text = response_text.strip()
        if len(response_text) > 50000:
            print("⚠️  Warning: LLM response exceeds maximum length and will be truncated.")
            response_text = response_text[:50000]
        
        extraction_methods = [
            self._extract_from_markdown,   
            self._extract_from_json_key, 
            self._extract_from_json_key,
            self._extract_from_boundaries,
            self._extract_direct_list,
            self._intelligent_repair,
            self._manual_json_repair
        ]
        
        for method in extraction_methods:
            try:
                plan = method(response_text)
                if plan is not None and self._validate_plan_is_structurally_sound(plan):
                    if method.__name__ not in ["_extract_from_markdown", "_extract_direct_list", "_extract_from_boundaries"]:
                         print(f"✅ Plan successfully recovered using '{method.__name__}' method.")
                    return plan
            except (json.JSONDecodeError, TypeError):
                continue

        print(f"⚠️  Warning: All JSON extraction and validation methods failed. Response preview (2000 chars):\n---\n{response_text[:2000]}...\n---")
        return []

    def _extract_from_markdown(self, text: str) -> Optional[List[Dict[str, Any]]]:
        pattern = r'```(?:json)?\s*(.*?)\s*```'
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return json.loads(matches[0])
        return None

    def _extract_from_json_key(self, text: str) -> Optional[List[Dict[str, Any]]]:
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                # Check for 'plan' as the primary key, then fall back
                for key in ["plan", "JSON_PLAN", "json_plan"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
        except (json.JSONDecodeError, TypeError):
            return None
        return None

    def _extract_from_boundaries(self, text: str) -> Optional[List[Dict[str, Any]]]:
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        return None

    def _extract_direct_list(self, text: str) -> Optional[List[Dict[str, Any]]]:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        return None

    def _intelligent_repair(self, text: str) -> Optional[List[Dict[str, Any]]]:
        if text.startswith('{'):
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    return [data]
            except json.JSONDecodeError:
                pass
        
        if re.match(r'^\s*\{.*\}\s*(,\s*\{.*\}\s*)*$', text, re.DOTALL):
            repaired_text = f'[{text}]'
            return json.loads(repaired_text)
            
        return None

    def _manual_json_repair(self, text: str) -> Optional[List[Dict[str, Any]]]:
        objects = []
        buffer = ""
        brace_count = 0
        in_string = False
        escape = False
        
        for char in text:
            if char == '"' and not escape:
                in_string = not in_string
            
            is_escape_char = (char == '\\')
            
            if not in_string:
                if char == '{':
                    if brace_count == 0:
                        buffer = ""
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
            
            if brace_count > 0:
                buffer += char
            elif brace_count == 0 and buffer:
                buffer += char
                try:
                    objects.append(json.loads(buffer))
                except json.JSONDecodeError:
                    pass
                buffer = ""
            
            escape = is_escape_char and not escape

        return objects if objects else None

    def _validate_plan_is_structurally_sound(self, plan: List[Dict[str, Any]]) -> bool:
        if isinstance(plan, list) and not plan:
            return True
        if not isinstance(plan, list): return False
        if len(plan) > 25: return False
        
        # Allow 'tool' as an alias for 'tool_name'
        for i, step in enumerate(plan):
            if not isinstance(step, dict): return False
            
            # Normalize 'tool' to 'tool_name'
            if 'tool' in step and 'tool_name' not in step:
                step['tool_name'] = step.pop('tool')

            if "tool_name" not in step or "args" not in step: return False
            
            tool_name = step["tool_name"]
            if tool_name and tool_name.lower() != "null" and not TOOL_REGISTRY.get_tool(tool_name):
                print(f"⚠️  Warning: Step {i+1} references unknown tool: '{tool_name}'. Rejecting plan.")
                return False
            
            # Validate optional condition structure
            if 'condition' in step:
                if not isinstance(step['condition'], dict): return False
                if not ('from_step' in step['condition'] and ('in' or 'not_in' in step['condition'])):
                    return False

        return True