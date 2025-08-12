# /scripts/validate_personas.py

import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List
import argparse 

# --- Third-party Imports ---
# Ensure 'pydantic' is in your requirements.txt
try:
    from pydantic import BaseModel, ValidationError, create_model
except ImportError:
    print("FATAL: Pydantic is not installed. Please run 'pip install pydantic'.", file=sys.stderr)
    sys.exit(1)

# --- Local Imports ---
from pel_utils import load_config, find_all_personas

# --- Constants ---

ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "persona_config.yml"
PERSONAS_DIR = ROOT_DIR / "src" / "ai_assistant" / "personas" # Define the canonical persona dir
GREEN, YELLOW, RED, BLUE, NC, GRAY = (
    "\033[92m", "\033[93m", "\033[91m", "\033[94m", "\033[0m", "\033[90m"
)

def parse_persona_body(body_content: str) -> Dict[str, str]:
    """
    Parses the body of a persona file into a dictionary of sections
    without using regular expressions.
    """
    sections = {}
    # Split the body by the opening tag of a section, ignoring anything before the first one.
    parts = body_content.split("<SECTION:")[1:]
    for part in parts:
        try:
            # The section name is up to the first '>', and the rest is content.
            name, content = part.split(">", 1)
            # Clean up the content by removing the closing tag and stripping whitespace.
            content = content.replace("</SECTION>", "").strip()
            sections[name.strip()] = content
        except ValueError:
            # Skip any malformed parts that don't contain a '>'.
            continue
    return sections

def validate_persona_file(
    data: Dict[str, Any],
    body: str,
    persona_type_rules: Dict[str, Any],
    body_schemas_by_type: Dict[str, List[str]],
):
    """
    Validates a single persona file against both frontmatter and body schema rules.
    """
    # 1. Validate Frontmatter
    persona_type = data.get("type")
    if not persona_type:
        return False, "Frontmatter: Missing required 'type' key."
    if persona_type not in persona_type_rules:
        return False, f"Frontmatter: Invalid persona type '{persona_type}'."
    rules = persona_type_rules[persona_type]
    required_keys = rules.get("required_keys", [])
    if not all(key in data for key in required_keys):
        missing = [key for key in required_keys if key not in data]
        return False, f"Frontmatter: Missing required keys for '{persona_type}': {missing}."

    # 2. Validate Persona Body based on its type
    required_sections = body_schemas_by_type.get(persona_type, [])
    if not required_sections:
        # If no sections are required for this type, skip body validation.
        return True, f"OK: {data.get('alias', 'N/A')} ({persona_type}) - Body validation skipped"

    try:
        # Dynamically create a Pydantic model from the config rules.
        # The '...' (Ellipsis) makes the fields required.
        PersonaBodyModel = create_model(
            'PersonaBodyModel',
            **{field: (str, ...) for field in required_sections}
        )
        # Parse the body and validate it against the dynamic model.
        parsed_body = parse_persona_body(body)
        
        # --- CHECK ---
        for section_name, section_content in parsed_body.items():
            if "[REFACTOR_NOTE:" in section_content:
                return False, f"Body Content: Section '{section_name}' contains a placeholder REFACTOR_NOTE."
        # --- END OF CHECK ---
    
        PersonaBodyModel(**parsed_body)
        
    except ValidationError as e:
        # Pydantic provides detailed, human-readable error messages.
        return False, f"Body Schema: Validation failed for type '{persona_type}'.\n       └─ {str(e).replace('__root__', '')}"
    except Exception as e:
        return False, f"Body Parser: Unexpected error during body parsing: {e}"

    return True, f"OK: {data.get('alias', 'N/A')} ({persona_type})"

def main(config: Dict[str, Any]) -> int:
    """Main validation function."""
    
    if not config: # ADDED: A check for a valid config object
        print(f"{RED}FATAL: Configuration object is empty or None. Cannot proceed.{NC}", file=sys.stderr)
        return 1
    
    active_stati = config.get("validation_rules", {}).get("active_stati", ["active"])
    persona_type_rules = config.get("persona_types", {})
    body_schemas_by_type = config.get("body_schemas_by_type", {})

    print(f"{BLUE}--- Starting Persona Validation (v7.0) ---{NC}")
    print(f"Validating only personas with status in: {active_stati}")
    if body_schemas_by_type:
        print("Enforcing body schemas based on persona type.\n")
    else:
        print("No body schemas defined in config, skipping all body validation.\n")

    all_persona_paths = find_all_personas(ROOT_DIR)
    if not all_persona_paths:
        print(f"{YELLOW}No persona files found. Validation skipped.{NC}")
        return 0

    error_count, success_count, skipped_count = 0, 0, 0
    for persona_path in all_persona_paths:
        relative_path = persona_path.relative_to(ROOT_DIR)
        try:
            # 1. Read the file and create 'parts' FIRST.
            content = persona_path.read_text(encoding="utf-8")
            parts = content.split("---")
            if len(parts) < 3:
                raise ValueError("File does not contain valid YAML frontmatter.")

            # 2. Now that 'parts' exists, parse the frontmatter.
            frontmatter_data = yaml.safe_load(parts[1])
            if not isinstance(frontmatter_data, dict):
                raise ValueError("YAML frontmatter is not a valid dictionary.")

            # 3. Perform the filename vs. alias check.
            expected_alias = persona_path.stem.replace('.persona', '')
            actual_alias = frontmatter_data.get("alias")
            # Compare both as lowercase to enforce the standard but allow flexibility in the file.
            if actual_alias.lower() != expected_alias.lower():
                raise ValueError(f"Filename-Alias Mismatch: File is '{expected_alias}.persona.md' but alias is '{actual_alias}'.")

            # 4. Perform the status check.
            if frontmatter_data.get("status") not in active_stati:
                print(f"{GRAY}[SKIP]{NC} {relative_path} (status: '{frontmatter_data.get('status')}')")
                skipped_count += 1
                continue

            # 5. Perform the full validation.
            persona_body = "---".join(parts[2:])
            is_valid, message = validate_persona_file(
                frontmatter_data, persona_body, persona_type_rules, body_schemas_by_type
            )

            if is_valid:
                print(f"{GREEN}[PASS]{NC} {relative_path}")
                success_count += 1
            else:
                raise ValueError(message) # Raise the specific error from the validator

        except (ValueError, yaml.YAMLError) as e:
            print(f"{RED}[FAIL]{NC} {relative_path}\n     └─ {YELLOW}Reason: {e}{NC}")
            error_count += 1

    print(f"\nValidation Summary: {GREEN}{success_count} passed, {RED}{error_count} failed, {GRAY}{skipped_count} skipped.{NC}")
    return error_count

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Validate persona files based on a config.")
    parser.add_argument(
        '--config',
        type=Path,
        default=ROOT_DIR / "persona_config.yml",
        help="Path to the persona configuration YAML file."
    )
    args = parser.parse_args()

    config_path = args.config.resolve()
    if not config_path.exists():
        print(f"{RED}FATAL: Config file not found at specified path: {config_path}{NC}", file=sys.stderr)
        sys.exit(1)

    print(f"{BLUE}--- Loading config from: {config_path} ---{NC}")
    loaded_config = load_config(config_path)
    final_error_count = main(loaded_config)
    sys.exit(1 if final_error_count > 0 else 0)