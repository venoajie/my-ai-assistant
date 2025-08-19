# Guide: The Persona System

The most powerful feature of the AI Assistant is its **Persona System**. Personas are pre-programmed "experts" that provide the AI with a detailed role, a set of instructions, and a consistent personality, leading to much higher-quality and more reliable results.

**Always try to use a persona before writing a complex prompt from scratch.**

## Finding Available Personas

You can list all built-in personas from the command line:
```bash
ai --list-personas
```

---

## Where Personas Live: Project-Local vs. User-Global

Personas can be defined in two locations, each with a specific purpose. Understanding this distinction is key to using them effectively.

| Location | Path | Use Case | Governance |
| :--- | :--- | :--- | :--- |
| **Project-Local** | `.ai/personas/` | **(Best Practice)** For project-specific experts that are shared with your team and committed to your project's Git repository. | Flexible, part of your project. |
| **User-Global** | `~/.config/ai_assistant/personas/` | For your own personal, private personas that you want to use across all of your projects. | Managed by you, not shared. |

For team-based software development, **using project-local personas is the recommended best practice** as it ensures every team member is working with the same set of AI experts.

---

## Creating a Project-Local Persona (Best Practice)

Let's create an expert for your project. This persona will live inside your project's repository and can be shared with your team.

1.  **Create the Directory:** In your project's root, create the necessary directories. The structure should mirror the built-in persona library.
    ```bash
    mkdir -p .ai/personas/domains/myproject
    ```

2.  **Create the Persona File:** Create a new file, for example: `.ai/personas/domains/myproject/api-designer-1.persona.md`.

3.  **Define the Persona:** The file uses a YAML "frontmatter" section and a body for instructions. The `alias` must match the file path relative to the `personas` directory, and it should `inherit_from` a suitable base persona.

    ```yaml
    ---
    alias: domains/myproject/api-designer-1
    version: 1.0.0
    type: domains
    title: API Designer (My Project)
    description: "Designs API endpoints that follow our project's specific conventions."
    inherits_from: _base/developer-agent-1 # Inherits the safe Git workflow
    ---
    <SECTION:CORE_PHILOSOPHY>
    All API endpoints in this project must be RESTful, use snake_case, and include OpenAPI documentation strings.
    </SECTION:CORE_PHILOSOPHY>
    
    <SECTION:PRIMARY_DIRECTIVE>
    Your goal is to design and generate Python FastAPI code for new API endpoints, ensuring they adhere to all project-specific conventions.
    </SECTION:PRIMARY_DIRECTIVE>
    
    <SECTION:OPERATIONAL_PROTOCOL>
    <Step number="1" name="Ingest Request">Receive a request for a new API endpoint.</Step>
    <Step number="2" name="Design Endpoint">Design the endpoint, including the path, HTTP method, and data model.</Step>
    <Step number="3" name="Generate Code">Generate the complete, documented Python code for the endpoint.</Step>
    </SECTION:OPERATIONAL_PROTOCOL>
    
    <SECTION:OUTPUT_CONTRACT>
    The output is a complete Python file containing the new FastAPI endpoint.
    </SECTION:OUTPUT_CONTRACT>
    ```

The AI Assistant will automatically discover this persona. You can now use it in your project:
```bash
ai --persona domains/myproject/api-designer-1 "Create a new endpoint to fetch user profiles."
```

> **Pro Tip:** To make your project-local personas even more powerful, you can combine them with a project configuration file to automatically provide them with the context they need. Learn more in the **[Project-Specific Configuration Guide](./project_configuration.md)**.

