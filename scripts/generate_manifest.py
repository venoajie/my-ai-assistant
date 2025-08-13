# /scripts/generate_manifest.py
# Version: 6.0 (Definitive - With Unified Validation)

import yaml
from pathlib import Path
from datetime import datetime, timezone
import sys
import re
import os 

from persona_validator import PersonaValidator

# Add src to path to import ai_assistant modules
ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "persona_config.yml"
sys.path.insert(0, str(ROOT_DIR / "src"))

# --- Constants ---
PERSONAS_DIR = ROOT_DIR / "src" / "ai_assistant" / "personas"
OUTPUT_FILE = ROOT_DIR / "persona_manifest.yml"
MANIFEST_VERSION = "1.5"


def extract_description(content: str) -> str:
    """
    Extracts a description by finding the first meaningful, non-empty line
    of text after the frontmatter.
    """
    body = content.split('---', 2)[-1]
    for line in body.splitlines():
        cleaned_line = line.strip()
        if cleaned_line and not (cleaned_line.startswith('<') and cleaned_line.endswith('>')):
            cleaned_line = re.sub(r'\[.*?\]', '', cleaned_line).strip()
            cleaned_line = cleaned_line.replace('*', '').replace('_', '').strip()
            if cleaned_line:
                return cleaned_line
    return "No descriptive line found."


def is_public_persona(persona_path: Path, personas_root: Path) -> bool:
    """
    Determines if a persona is public by checking if any part of its
    path relative to the root contains a directory starting with '_'.
    """
    relative_path = persona_path.relative_to(personas_root)
    return not any(part.startswith('_') for part in relative_path.parts)


def main():
    """
    Scans all persona files, performs critical validation (including alias matching),
    filters for public personas, and generates the persona_manifest.yml file.
    This script is now the single source of truth for build-time validation.
    """
    print("--- Generating Persona Manifest (v6.0 - Definitive) ---")
    print(f"Scanning for personas in: {PERSONAS_DIR}")

    all_personas = list(PERSONAS_DIR.rglob("*.persona.md"))
    validator = PersonaValidator(CONFIG_FILE) 
    manifest_personas = []
    has_errors = False

    for persona_path in all_personas:
        
        is_valid, reason = validator.validate_persona(persona_path, PERSONAS_DIR)
        if not is_valid:
            print(f"  - [FAIL] {persona_path.relative_to(ROOT_DIR)}", file=sys.stderr)
            print(f"       └─ Reason: {reason}", file=sys.stderr)
            has_errors = True
            continue
        
        try:
            content = persona_path.read_text(encoding="utf-8")
            parts = content.split("---")
            if len(parts) < 3:
                print(f"  - [FAIL] Malformed persona file (missing '---' separators): {persona_path}", file=sys.stderr)
                has_errors = True
                continue

            data = yaml.safe_load(parts[1])
            if not isinstance(data, dict) or "alias" not in data or "title" not in data:
                print(f"  - [FAIL] Invalid or missing frontmatter (requires 'alias' and 'title'): {persona_path}", file=sys.stderr)
                has_errors = True
                continue

            # --- UNIFIED VALIDATION LOGIC ---
            expected_alias = str(persona_path.relative_to(PERSONAS_DIR)).replace(".persona.md", "").replace(os.path.sep, "/")
            actual_alias = data.get("alias")
            if expected_alias.lower() != actual_alias.lower():
                print(f"  - [FAIL] Filename-Alias Mismatch in {persona_path}:", file=sys.stderr)
                print(f"       └─ Expected alias based on path: '{expected_alias}'", file=sys.stderr)
                print(f"       └─ Found alias in frontmatter:   '{actual_alias}'", file=sys.stderr)
                has_errors = True
                continue # Do not add invalid personas to the manifest
            # --- END OF UNIFIED VALIDATION ---

            if is_public_persona(persona_path, PERSONAS_DIR):
                description = extract_description(content)
                manifest_personas.append(
                    {
                        "alias": actual_alias,
                        "title": data.get("title"),
                        "description": description,
                    }
                )
        except (yaml.YAMLError, Exception) as e:
            print(f"  - [FAIL] Error processing {persona_path}: {e}", file=sys.stderr)
            has_errors = True
            continue

    if has_errors:
        print("\n🛑 Validation failed. Persona manifest was NOT generated.", file=sys.stderr)
        sys.exit(1)

    manifest_personas.sort(key=lambda p: p["alias"])
    manifest_data = {
        "version": MANIFEST_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "personas": manifest_personas,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(manifest_data, f, sort_keys=False, indent=2, default_flow_style=False)

    print(f"\n✓ All personas passed validation.")
    print(f"✓ Persona manifest successfully generated at: {OUTPUT_FILE}")
    print(f"  Found and included {len(manifest_personas)} public personas.")


if __name__ == "__main__":
    main()