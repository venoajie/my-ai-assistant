# /scripts/generate_manifest.py
# Version: 7.0 (Definitive - With Unified Validation)

import yaml
from pathlib import Path
from datetime import datetime, timezone
import sys
import re
import os 
import hashlib
import json

from persona_validator import PersonaValidator

# Add src to path to import ai_assistant modules
ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "persona_config.yml"
sys.path.insert(0, str(ROOT_DIR / "src"))

# --- Constants ---
PERSONAS_DIR = ROOT_DIR / "src" / "ai_assistant" / "personas"
OUTPUT_FILE = ROOT_DIR / "persona_manifest.yml"
MANIFEST_VERSION = "2.0"


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
    Scans, validates all personas, and generates a cryptographically signed
    persona_manifest.yml file only on complete success.
    """
    print("--- Generating Persona Manifest (v7.0 - With Cryptographic Signature) ---")
    print(f"Scanning for personas in: {PERSONAS_DIR}")

    all_personas = list(PERSONAS_DIR.rglob("*.persona.md"))
    validator = PersonaValidator(CONFIG_FILE)
    validated_persona_details = []
    has_errors = False

    for persona_path in all_personas:
        is_valid, reason = validator.validate_persona(persona_path, PERSONAS_DIR)
        if not is_valid:
            print(f"  - [FAIL] {persona_path.relative_to(ROOT_DIR)}", file=sys.stderr)
            print(f"       └─ Reason: {reason}", file=sys.stderr)
            has_errors = True
        else:
            # Collect details of valid personas for signature generation
            content = persona_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content.split("---")[1])
            validated_persona_details.append({
                "path": persona_path,
                "alias": data['alias'],
                "title": data.get('title'),
                "content": content,
            })

    if has_errors:
        print("\n🛑 Validation failed. Persona manifest was NOT generated.", file=sys.stderr)
        sys.exit(1)

    # --- SIGNATURE GENERATION ---
    # 1. Create a canonical data structure of all validated personas
    canonical_data = []
    for details in sorted(validated_persona_details, key=lambda p: p['alias']):
        canonical_data.append({
            "alias": details['alias'],
            "path": str(details['path'].relative_to(ROOT_DIR)),
            "content_sha256": hashlib.sha256(details['content'].encode('utf-8')).hexdigest()
        })

    # 2. Create a stable string representation and hash it
    canonical_string = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
    validation_signature = hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()

    # --- MANIFEST CREATION ---
    # Filter for public personas to be listed in the manifest
    public_personas = []
    for details in validated_persona_details:
        if is_public_persona(details['path'], PERSONAS_DIR):
            description = extract_description(details['content'])
            public_personas.append({
                "alias": details['alias'],
                "title": details['title'],
                "description": description,
            })

    public_personas.sort(key=lambda p: p["alias"])
    manifest_data = {
        "version": MANIFEST_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation_signature": validation_signature, # Embed the signature
        "personas": public_personas,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(manifest_data, f, sort_keys=False, indent=2, default_flow_style=False)

    print(f"\n✓ All {len(all_personas)} personas passed validation.")
    print(f"✓ Persona manifest successfully generated at: {OUTPUT_FILE}")
    print(f"  - Included {len(public_personas)} public personas in the list.")
    print(f"  - Validation Signature: {validation_signature[:12]}...")


if __name__ == "__main__":
    main()