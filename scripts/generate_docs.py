# scripts/generate_docs.py
import yaml
from pathlib import Path

def main():
    """
    Generates final documentation files from templates and a central
    governance file to prevent documentation drift.
    """
    project_root = Path(__file__).parent.parent.resolve()
    governance_file = project_root / "src" / "ai_assistant" / "internal_data" / "governance.yml"
    template_dir = project_root / "docs" / "templates"
    output_dir = project_root / "docs"

    print("--- Generating Documentation from Templates ---")

    # 1. Load the single source of truth
    with open(governance_file, 'r', encoding='utf-8') as f:
        rules = yaml.safe_load(f)

    risky_keywords = rules.get("prompting_best_practices", {}).get("risky_modification_keywords", [])
    
    # 2. Format the data for insertion into Markdown
    # Example output: `refactor`, `fix`, `modify`
    keyword_list_str = ", ".join(f"`{word}`" for word in risky_keywords)

    # 3. Process the template file
    template_path = template_dir / "prompting_guide.md.template"
    output_path = output_dir / "prompting_guide.md"

    print(f"  - Processing template: {template_path.relative_to(project_root)}")
    content = template_path.read_text(encoding='utf-8')
    
    # 4. Replace the placeholder with the generated list
    content = content.replace("{{RISKY_KEYWORDS_LIST}}", keyword_list_str)

    # 5. Write the final documentation file
    output_path.write_text(content, encoding='utf-8')
    print(f"  ✅ Generated: {output_path.relative_to(project_root)}")

    print("\nDocumentation generation complete.")

if __name__ == "__main__":
    main()