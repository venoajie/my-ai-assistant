# my-ai-assistance

# AI Assistant - Developer's Guide

![AI Assistant Architecture](https://via.placeholder.com/800x400?text=AI+Assistant+Architecture+Diagram)

A general-purpose AI assistant for software development that helps with coding, debugging, architectural reviews, and task automation. Originally built for trading applications, it now supports any software project with optional domain-specific extensions.

## Key Features
- **Conversational Interface**: Interactive sessions with memory
- **Persona System**: Specialized expert profiles (SA-1, QTSA-1, ADA-1)
- **File Awareness**: Read, analyze, and modify source code
- **Autonomous Mode**: Automated task execution (use with caution)
- **Plugin System**: Domain-specific context (e.g., trading)
- **Configuration Layers**: Default → User → Project settings

## Installation
```bash
pip install my-ai-assistant

Configuration System
The assistant uses a layered configuration approach:

1. Default Configuration
Location: Bundled with package

Purpose: Core settings and fallback values

Never modify directly - use overrides instead

2. User Configuration
Location: ~/.config/ai_assistant/config.yml

Purpose: Personal preferences and secrets

Example content:
general:
  sessions_directory: "~/.ai_sessions"  # Custom session storage
  max_context_files: 5                  # Limit attached files

generation_params:
  synthesis:
    temperature: 0.3                    # More creative responses

providers:
  gemini:
    api_key_env: "MY_GEMINI_KEY"        # Your personal API key


3. Project Configuration
Location: ./.ai_config.yml (project root)

Purpose: Project-specific settings

Example content:
# .ai_config.yml
trading:
  exchanges: ["binance", "deribit"]
  services:
    - name: "receiver"
      purpose: "Market data ingestion"
    - name: "distributor" 
      purpose: "Real-time data distribution"

assistant:
  trading_domain_knowledge: true        # Enable trading context

Configuration Priority
Project config (.ai_config.yml)

User config (~/.config/ai_assistant/config.yml)

Package defaults

Basic Usage
ai [FLAGS] "Your goal in plain English"

Core Flags
Flag	Description	Example
--new-session	Start new session	ai --new-session "Debug login issue"
--session <ID>	Continue session	ai --session a1b2c3d4
--persona <NAME>	Use expert persona	ai --persona domains/trading/QTSA-1
-f, --file <PATH>	Attach file to context	ai -f src/main.py "Explain this code"
--context <PLUGIN>	Load context plugin	ai --context Trading "Analyze order flow"
--autonomous	Enable auto-execution	ai --autonomous "Refactor service"
Persona System
Core Personas
Alias	Specialty	Use Case
core/SA-1	Systems Architecture	Service design, Docker configs
core/DA-1	Debugging Assistance	Error diagnosis, stack traces
core/CA-1	Code Analysis	Code reviews, optimizations
Domain-Specific Personas
Alias	Domain	Specialty
domains/trading/QTSA-1	Trading	Strategy development
domains/finance/ADA-1	Finance	API contract design
domains/web/FEA-1	Web	Frontend architecture
Using Personas
# General system design
ai --persona core/SA-1 "Design microservice architecture"

# Trading-specific analysis
ai --persona domains/trading/QTSA-1 --context Trading "Optimize backtest engine"


Context Plugins
Built-in Plugins
Trading: Market data concepts, exchange protocols

Web: HTTP semantics, REST best practices

Data: ETL patterns, dataframe optimizations

Activating Plugins
ai --context Trading "Explain market data flow"


Creating Custom Plugins
Create plugins/my_domain.py:

from ai_assistant.context_plugin import ContextPluginBase

class MyDomainPlugin(ContextPluginBase):
    name = "MyDomain"
    
    def get_context(self, query: str, files: List[str]) -> str:
        if "domain_term" in query:
            return "<MyDomainKnowledge>...</MyDomainKnowledge>"
        return ""

Reference in commands:
ai --context MyDomain "Analyze domain-specific issue"

Session Management
Sessions preserve conversation history across commands.

Starting a Session
bash
ai --new-session --persona core/SA-1 "Design auth service"
Output:

text
✨ Starting new session: a1b2c3d4-e5f6-7890-gh12-i3j4k5l6m7n8
Continuing a Session
bash
ai --session a1b2c3d4-e5f6-7890-gh12-i3j4k5l6m7n8 "Add rate limiting"
Session Storage
Default: ~/.ai_sessions/

Configure via general.sessions_directory in config

Autonomous Mode
Use with extreme caution! Allows full file system access.

bash
ai --autonomous --persona core/SA-1 \
   -f Dockerfile \
   "Optimize Docker build and push to Git branch"
Safety Guards
Blocks dangerous shell patterns (rm -rf /, format)

Requires confirmation for risky operations

File operations sandboxed to project directory

Advanced Workflows
Multi-File Analysis
bash
ai "Compare these service implementations" \
  -f services/auth/service.py \
  -f services/payment/service.py
Architectural Review
bash
ai "Review architecture against cloud best practices" \
  -f docs/architecture.md \
  -f terraform/main.tf \
  -f docker-compose.yml
Code Generation
bash
ai --persona core/SA-1 \
   "Create Python class for Redis cache manager" \
   > caching.py
Troubleshooting
Common Issues
Symptom	Solution
Missing API keys	Set environment variables per providers config
Session not found	Check general.sessions_directory path
Plugin not loading	Ensure plugin file is in plugins/ directory
File attachment failed	Verify file exists and path is relative to project root
Getting Help
bash
ai "help"  # Get built-in assistance
Contribution Guidelines
Place new personas in personas/ directory

Put domain plugins in plugins/

Update .ai_config.yml for project-specific settings

Submit PRs to github.com/your-repo

API Key Management Guide
Add this section to your README.md:

markdown
## API Key Management & Security

The AI Assistant requires API keys for AI providers. Follow these security best practices:

### 1. Environment Variables (Recommended)
```bash
# Linux/Mac
export GEMINI_API_KEY="your_actual_key"
export DEEPSEEK_API_KEY="your_actual_key"

# Windows
set GEMINI_API_KEY=your_actual_key
set DEEPSEEK_API_KEY=your_actual_key
2. Configuration File (User Directory)
Create ~/.config/ai_assistant/config.yml:

yaml
providers:
  gemini:
    api_key: "your_actual_key"
  deepseek:
    api_key: "your_actual_key"
⚠️ Never commit actual keys to version control!

3. CI/CD Secrets Management
For GitHub Actions:

Go to Repository Settings > Secrets > Actions

Add:

GEMINI_API_KEY

DEEPSEEK_API_KEY

PYPI_API_TOKEN (for package publishing)

4. Security Considerations
Never store keys in project files - Use environment variables or user config

Rotate keys regularly - Especially if leaked

Use provider key restrictions:

Gemini: Set application restrictions

DeepSeek: Enable IP whitelisting

Monitor usage - Set up billing alerts

5. Testing with Mock Keys
For safe testing, use mock keys:

python
# tests/test_config.py
class MockConfig:
    providers = {
        "gemini": {"api_key": "test-key"},
        "deepseek": {"api_key": "test-key"}
    }
    
ai_settings = MockConfig()
6. Key Rotation Procedure
Generate new keys in provider dashboards

Update environment variables/user config

Revoke old keys

Test with ai "What's my API key status?"

text

### Required Files
1. **setup.py** (for package installation):
```python: setup.py
from setuptools import setup, find_packages

setup(
    name="my-ai-assistant",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28",
        "pyyaml>=6.0",
        "pydantic>=2.0"
    ],
    extras_require={
        "test": ["unittest2", "coverage"]
    },
    package_data={
        "ai_assistant": ["personas/**/*.md"],
    },
    entry_points={
        "console_scripts": [
            "ai=ai_assistant.cli:main",
        ],
    },
)
Test Dependencies (requirements-test.txt):

text
unittest2
coverage
Pipeline Features
Multi-stage Workflow:

Unit tests on 3 Python versions

Security validation

Integration testing

Automated publishing

Quality Gates:

Tests must pass before build

Coverage reporting

Security scanning

Release Automation:

Auto-publishes to PyPI on release creation

Generates release notes

Attaches build artifacts

Secret Handling:

Encrypted API keys in CI

Never exposed in logs

Scoped to required jobs

Usage Workflow
Development:

bash
# Run tests locally
python -m unittest discover tests -v

# Check coverage
coverage run -m unittest discover
coverage report
CI/CD Process:

Diagram
graph TD
    A[Push/Pull Request] --> B[Run Tests]
    B --> C{All Pass?}
    C -->|Yes| D[Main Branch]
    C -->|No| E[Fail Fast]
    D --> F[Release Tag]
    F --> G[Build Package]
    G --> H[Publish to PyPI]



Release Management:
# Create new release
git tag -a v1.1.0 -m "Production release"
git push origin v1.1.0

This setup provides:

Comprehensive testing before deployment

Secure API key handling

Automated release pipeline

Multi-environment validation

Security scanning for dangerous commands

Seamless package publishing

The API key management guide ensures developers:

Understand secure handling practices

Can configure keys safely across environments

Know how to rotate compromised keys

Can test safely without exposing real credentials

Version: 1.0.0