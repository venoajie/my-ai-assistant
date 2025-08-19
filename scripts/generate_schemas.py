# scripts/generate_schemas.py
import yaml
import json
from pathlib import Path
import sys

def main():
    """
    Generates formal JSON schema files from the master system_contracts.yml document.
    This ensures that our documentation is the single source of truth for data contracts.
    """
    project_root = Path(__file__).parent.parent.resolve()
    contracts_file = project_root / "docs" / "system_contracts.yml"
    schemas_dir = project_root / "src" / "ai_assistant" / "internal_data" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    print("--- Generating JSON Schemas from System Contracts ---")
    print(f"Source: {contracts_file.relative_to(project_root)}")

    try:
        with open(contracts_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"❌ FATAL: Could not load or parse {contracts_file}. Error: {e}", file=sys.stderr)
        sys.exit(1)

    contracts_to_generate = {
        "Output Package Manifest": "output_package_manifest_schema.json",
    }
    
    generated_count = 0
    
    # --- THIS IS THE FIX ---
    # Combine all contracts from the different sections of the YAML file.
    all_contracts = data.get("persistent_contracts", []) + data.get("process_artifacts", [])
    if not all_contracts:
        print("⚠️  Warning: No 'persistent_contracts' or 'process_artifacts' found in the source file.", file=sys.stderr)
        sys.exit(0)

    for contract in all_contracts:
        contract_name = contract.get("name")
        if contract_name in contracts_to_generate:
            schema_def = contract.get("schema_definition")
            if not schema_def:
                print(f"⚠️  Warning: Skipping '{contract_name}' as it has no 'schema_definition' block.", file=sys.stderr)
                continue

            output_filename = contracts_to_generate[contract_name]
            output_path = schemas_dir / output_filename
            
            # Add standard schema header
            full_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": f"AI Assistant {contract_name}",
                "description": contract.get("description", ""),
                **schema_def
            }

            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(full_schema, f, indent=2)
                print(f"  ✅ Generated: {output_path.relative_to(project_root)}")
                generated_count += 1
            except IOError as e:
                print(f"❌ FATAL: Could not write to {output_path}. Error: {e}", file=sys.stderr)
                sys.exit(1)

    print(f"\nSuccessfully generated {generated_count} schema file(s).")

if __name__ == "__main__":
    main()