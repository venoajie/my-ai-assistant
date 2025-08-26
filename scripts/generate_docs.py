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
    config_file = project_root / "src" / "ai_assistant" / "default_config.yml"
    template_dir = project_root / "docs" / "templates"
    output_dir = project_root / "docs"

    print("--- Generating Documentation from Templates ---")

    # 1. Load the sources of truth
    with open(governance_file, 'r', encoding='utf-8') as f:
        governance_data = yaml.safe_load(f)
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 2. Format data for insertion into Markdown
    
    # Process risky keywords from the unified governance file
    risky_keywords = governance_data.get("prompting_best_practices", {}).get("risky_modification_keywords", [])
    keyword_list_str = ", ".join(f"`{word}`" for word in risky_keywords)

    # Process model configuration
    model_selection = config.get("model_selection", {})
    default_provider = config.get("default_provider", "N/A")
    models_info_parts = [
        f"The AI Assistant is configured by default to use models from the **`{default_provider.capitalize()}`** provider. You will need to acquire an API key from the respective provider and set it as an environment variable to run the assistant.",
        "The default models for core tasks are:",
        f"- **Planning:** `{model_selection.get('planning', 'N/A')}`",
        f"- **Critique:** `{model_selection.get('critique', 'N/A')}`",
        f"- **Synthesis:** `{model_selection.get('synthesis', 'N/A')}`"
    ]
    models_info_str = "\n".join(models_info_parts)

    # Process analyzer rules from the unified governance file
    analyzer_rules_list = governance_data.get("prompt_analysis_rules", [])
    analyzer_rules_parts = []
    for rule in analyzer_rules_list:
        analyzer_rules_parts.append(f"-   **{rule['name']}:** {rule['description']}")
    analyzer_rules_str = "\n".join(analyzer_rules_parts)

    # 3. Process the template file
    template_path = template_dir / "prompting_guide.md.template"
    output_path = output_dir / "prompting_guide.md"

    print(f"  - Processing template: {template_path.relative_to(project_root)}")
    content = template_path.read_text(encoding='utf-8')
    
    # 4. Replace placeholders
    content = content.replace("{{RISKY_KEYWORDS_LIST}}", keyword_list_str)
    content = content.replace("{{DEFAULT_MODELS_INFO}}", models_info_str)
    content = content.replace("{{PROMPT_ANALYZER_RULES_LIST}}", analyzer_rules_str)

    # 5. Write the final documentation file
    output_path.write_text(content, encoding='utf-8')
    print(f"  ✅ Generated: {output_path.relative_to(project_root)}")

    print("\nDocumentation generation complete.")

if __name__ == "__main__":
    main()