# /scripts/validate_personas.py
# Version: 8.0 (Definitive - Unified Thin Client)

import sys
from pathlib import Path
import argparse

# This script is now a thin client for the shared validator.
from persona_validator import PersonaValidator

# --- Constants ---
ROOT_DIR = Path(__file__).parent.parent
DEFAULT_CONFIG_FILE = ROOT_DIR / "persona_config.yml"
PERSONAS_DIR = ROOT_DIR / "src" / "ai_assistant" / "personas"
GREEN, YELLOW, RED, BLUE, NC, GRAY = (
    "\033[92m", "\033[93m", "\033[91m", "\033[94m", "\033[0m", "\033[90m"
)

def find_all_personas(root_path: Path) -> list[Path]:
    """Finds all persona files in the canonical directory."""
    if not root_path.exists():
        return []
    return list(root_path.rglob("*.persona.md"))

def main() -> int:
    """
    Main entry point for the validation script.
    Parses arguments, instantiates the shared validator, and reports results.
    """
    parser = argparse.ArgumentParser(description="Validate all persona files against a canonical config.")
    parser.add_argument(
        '--config',
        type=Path,
        default=DEFAULT_CONFIG_FILE,
        help=f"Path to the persona configuration YAML file. Defaults to {DEFAULT_CONFIG_FILE}"
    )
    args = parser.parse_args()

    config_path = args.config.resolve()
    print(f"{BLUE}--- Starting Persona Validation (v8.0 - Unified) ---{NC}")
    print(f"Using config file: {config_path}")

    try:
        validator = PersonaValidator(config_path)
    except (FileNotFoundError, Exception) as e:
        print(f"{RED}FATAL: Could not initialize validator: {e}{NC}", file=sys.stderr)
        return 1

    all_persona_paths = find_all_personas(PERSONAS_DIR)
    if not all_persona_paths:
        print(f"{YELLOW}No persona files found in {PERSONAS_DIR}. Validation skipped.{NC}")
        return 0

    failure_count = 0
    success_count = 0

    for persona_path in sorted(all_persona_paths):
        relative_path = persona_path.relative_to(ROOT_DIR)
        is_valid, reason = validator.validate_persona(persona_path, PERSONAS_DIR)

        if is_valid:
            print(f"{GREEN}[PASS]{NC} {relative_path}")
            success_count += 1
        else:
            print(f"{RED}[FAIL]{NC} {relative_path}")
            print(f"     └─ {YELLOW}Reason: {reason}{NC}")
            failure_count += 1

    print(f"\nValidation Summary: {GREEN}{success_count} passed, {RED}{failure_count} failed.{NC}")
    return failure_count

if __name__ == "__main__":
    # The script returns an exit code of 0 on success and > 0 on failure,
    # which is standard practice for CI/CD integration.
    error_count = main()
    sys.exit(1 if error_count > 0 else 0)