# /scripts/generate_manifest.py
# Version: 5.0 (Final - With Public/Private Boundary Enforcement)

import yaml
from pathlib import Path
from datetime import datetime, timezone
import sys
import re

# Add src to path to import ai_assistant modules
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

# --- Constants ---
PERSONAS_DIR = ROOT_DIR / "src" / "ai_assistant" / "personas"
OUTPUT_FILE = ROOT_DIR / "persona_manifest.yml"
MANIFEST_VERSION = "1.4"


def extract_description(content: str) -> str:
    """
    Extracts a description by finding the first meaningful, non-empty line
    of text after the frontmatter.
    """
    body = content.split('---', 2)[-1]
    for line in body.splitlines():
        cleaned_line = line.strip()
        if cleaned_line and not (cleaned_line.startswith('<') and cleaned_line.endswith('>')):
            cleaned_line = re.sub(r'\[.*?\]', '', cleaned_line).strip() # Remove [REFACTOR_NOTE]
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
    Scans all persona files, validates their structure, filters for only
    PUBLIC personas, and generates the persona_manifest.yml file.
    """
    print("--- Generating Persona Manifest (v5.0 - Final) ---")
    print(f"Scanning for personas in: {PERSONAS_DIR}")

    all_personas = list(PERSONAS_DIR.rglob("*.persona.md"))
    manifest_personas = []

    for persona_path in all_personas:
        # --- THE CRITICAL GATEKEEPER LOGIC ---
        if not is_public_persona(persona_path, PERSONAS_DIR):
            print(f"  - Skipping private persona: {persona_path.relative_to(ROOT_DIR)}")
            continue
        # --- END OF GATEKEEPER LOGIC ---

        try:
            content = persona_path.read_text(encoding="utf-8")
            parts = content.split("---")
            if len(parts) < 3:
                print(f"  - FATAL: Malformed persona file: {persona_path}", file=sys.stderr)
                sys.exit(1)

            data = yaml.safe_load(parts[1])
            if not isinstance(data, dict) or "alias" not in data or "title" not in data:
                print(f"  - FATAL: Invalid frontmatter: {persona_path}", file=sys.stderr)
                sys.exit(1)

            description = extract_description(content)
            manifest_personas.append(
                {
                    "alias": data.get("alias"),
                    "title": data.get("title"),
                    "description": description,
                }
            )
        except (yaml.YAMLError, Exception) as e:
            print(f"  - FATAL: Error processing {persona_path}: {e}", file=sys.stderr)
            sys.exit(1)

    manifest_personas.sort(key=lambda p: p["alias"])

    manifest_data = {
        "version": MANIFEST_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "personas": manifest_personas,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(manifest_data, f, sort_keys=False, indent=2, default_flow_style=False)

    print(f"\n✓ Persona manifest successfully generated at: {OUTPUT_FILE}")
    print(f"  Found and included {len(manifest_personas)} public personas.")


if __name__ == "__main__":
    main()