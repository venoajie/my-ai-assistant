# Guide: The Persona System

The most powerful feature of the AI Assistant is its **Persona System**. Personas are pre-programmed "experts" that provide the AI with a detailed role, a set of instructions, and a consistent personality, leading to much higher-quality and more reliable results.

**Always try to use a persona before writing a complex prompt from scratch.**

## Finding Available Personas

You can list all built-in and project-local personas from the command line:
```bash
ai --list-personas
```

---

## The Directory Structure: A Critical Convention

The AI Assistant uses a conventional directory structure to organize personas by their function. Adhering to this convention is a best practice that ensures clarity and maintainability.

| Top-Level Directory | Purpose |
| :--- | :--- |
| `domains/` | Contains **specialist** personas that perform specific tasks (e.g., programming, writing, your project's specific needs). |
| `core/` | Reserved for personas that manage the AI Assistant itself or orchestrate workflows. |
| `_base/` | Foundational archetypes that define core behaviors (e.g., interactive vs. one-shot). All specialists should inherit from a base. |
| `_mixins/` | Reusable sets of directives (like coding standards) that can be inherited by any persona. |

When creating project-local personas, you should **always mirror this structure** inside your project's `.ai/personas/` directory.

---

## Creating a Project-Local Persona (Best Practice)

Let's create an expert for a new "cooking" domain. This demonstrates how to follow the conventions and extend the assistant's capabilities.

1.  **Create the Directory:** In your project's root, create a directory that follows the `domains/<your_new_domain>/` pattern.
    ```bash
    mkdir -p .ai/personas/domains/cooking
    ```

2.  **Create the Persona File:** Create your new persona file inside this directory.
    
    **File Path:** `.ai/personas/domains/cooking/recipe-generator-1.persona.md`

3.  **Define the Persona:** The `alias` in the file's frontmatter **must** match the file path relative to the `personas` directory.

    ```yaml
    ---
    alias: domains/cooking/recipe-generator-1
    version: 1.0.0
    type: domains
    title: Recipe Generator
    description: "Generates recipes based on a list of ingredients."
    inherits_from: _base/bcaa-1 # Inherits the collaborative protocol (propose a plan, then execute)
    ---
    <SECTION:CORE_PHILOSOPHY>
    A good recipe is clear, simple, and uses only the available ingredients.
    </SECTION:CORE_PHILOSOPHY>
    
    <SECTION:PRIMARY_DIRECTIVE>
    To generate a clear, step-by-step recipe using only the ingredients provided by the user.
    </SECTION:PRIMARY_DIRECTIVE>
    
    <SECTION:OPERATIONAL_PROTOCOL>
    <Step number="1" name="List Ingredients">Ask the user for a list of available ingredients.</Step>
    <Step number="2" name="Propose Recipe">Suggest a recipe that can be made with those ingredients and ask for confirmation.</Step>
    <Step number="3" name="Generate Recipe">Upon confirmation, generate the complete, step-by-step recipe.</Step>
    </SECTION:OPERATIONAL_PROTOCOL>
    
    <SECTION:OUTPUT_CONTRACT>
    The output is a well-formatted Markdown recipe.
    </SECTION:OUTPUT_CONTRACT>
    ```

The AI Assistant will automatically discover this new persona in its new domain. You can now use it in your project:
```bash
ai --persona domains/cooking/recipe-generator-1 "I have chicken, rice, and broccoli. What can I make?"
```

> **Pro Tip:** Manually typing `--persona` works, but the best practice is to automate it. Learn how to set a default persona and automatically provide it with critical context in the **[Project-Specific Configuration Guide](./project_configuration.md)**.
```
