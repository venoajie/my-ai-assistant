# scripts\generate_manifest.py

import yaml
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import sys

# This script now directly imports the validator from its own directory.
from persona_validator import PersonaValidator


class ManifestGenerator:
    """
    Validates all persona files and generates a manifest with a cryptographic signature.
    This script is IDEMPOTENT: it will not rewrite the manifest if the content
    of the persona files has not changed.
    """
    MANIFEST_VERSION = "7.2-filtered"

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.personas_dir = self.project_root / "src" / "ai_assistant" / "personas"
        self.config_path = self.project_root / "persona_config.yml"
        self.validator = PersonaValidator(self.config_path)

    def run(self):
        print(f"--- Generating Persona Manifest (v{self.MANIFEST_VERSION}) ---")
        print(f"Scanning for personas in: {self.personas_dir.relative_to(self.project_root)}")

        all_persona_paths = sorted(list(self.personas_dir.rglob("*.persona.md")))
        if not all_persona_paths:
            print("ERROR: No persona files found.", file=sys.stderr)
            sys.exit(1)

        validated_persona_details = []
        for persona_path in all_persona_paths:
            is_valid, reason = self.validator.validate_persona(persona_path, self.personas_dir)
            if not is_valid:
                print(f"\n🛑 HALTING: Persona validation failed for '{persona_path.relative_to(self.project_root)}'.", file=sys.stderr)
                print(f"   Reason: {reason}", file=sys.stderr)
                sys.exit(1)
            
            content = persona_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content.split("---")[1])
            validated_persona_details.append({
                "path": persona_path,
                "alias": data['alias'],
                "type": data['type'], # Store the type for filtering
                "title": data.get('title', 'N/A'),
                "description": data.get('description', 'No description provided.'),
                "content": content,
            })
        
        print(f"\n✓ All {len(validated_persona_details)} personas passed validation.")

        # --- IDEMPOTENCY CHECK ---
        new_signature = self._calculate_signature(validated_persona_details)
        manifest_path = self.project_root / "persona_manifest.yml"
        
        if self._is_manifest_up_to_date(manifest_path, new_signature):
            print("\n✓ Manifest is already up-to-date. No changes needed.")
            print(f"  - Validation Signature: {new_signature[:12]}...")
            return

        print("\nℹ️ Persona changes detected or manifest is missing/corrupted. Regenerating...")
        self._write_manifest(manifest_path, new_signature, validated_persona_details)
        
        public_personas_count = sum(1 for p in validated_persona_details if not p['type'].startswith('_'))
        print(f"✓ Persona manifest successfully generated at: {manifest_path.relative_to(self.project_root)}")
        print(f"  - Included {public_personas_count} public personas in the list.")
        print(f"  - Validation Signature: {new_signature[:12]}...")

    def _calculate_signature(self, persona_details: list) -> str:
        """Calculates a deterministic signature based on persona content and structure."""
        canonical_data = []
        for details in sorted(persona_details, key=lambda p: p['alias']):
            canonical_data.append({
                "alias": details['alias'],
                "path": str(details['path'].relative_to(self.project_root)),
                "content_sha256": hashlib.sha256(details['content'].encode('utf-8')).hexdigest()
            })
        
        canonical_string = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()

    def _is_manifest_up_to_date(self, manifest_path: Path, new_signature: str) -> bool:
        """Checks if the on-disk manifest exists and has the same signature."""
        if not manifest_path.exists():
            return False
        
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f)
            if not isinstance(existing_data, dict):
                return False
            existing_signature = existing_data.get("validation_signature")
            return existing_signature == new_signature
        except (yaml.YAMLError, TypeError):
            return False

    def _write_manifest(self, manifest_path: Path, signature: str, persona_details: list):
        """Builds and writes the final manifest YAML file, filtering for public personas."""
        public_personas = []
        for details in sorted(persona_details, key=lambda p: p['alias']):
            # CRITICAL FIX: Only include personas whose type does NOT start with '_'.
            if not details['type'].startswith('_'):
                public_personas.append({
                    "alias": details['alias'],
                    "title": details['title'],
                    "description": details['description'],
                })

        manifest_data = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "manifest_version": self.MANIFEST_VERSION,
            "validation_signature": signature,
            "personas": public_personas,
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(manifest_data, f, default_flow_style=False, sort_keys=False, indent=2)

if __name__ == "__main__":
    # Ensure the script can be run from the project root
    project_root_path = Path(__file__).parent.parent.resolve()
    sys.path.insert(0, str(project_root_path))
    
    generator = ManifestGenerator(project_root_path)
    generator.run()