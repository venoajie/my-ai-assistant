# src/ai_assistant/result_presenter.py
import re
import yaml
from importlib import resources

from .colors import Colors


try:
    governance_text = resources.files('ai_assistant').joinpath('internal_data/governance.yml').read_text(encoding='utf-8')
    GOVERNANCE_RULES = yaml.safe_load(governance_text)
    CRITICAL_KEYWORDS = GOVERNANCE_RULES.get("adversarial_critique", {}).get("critical_keywords", [])
    # Create a case-insensitive regex pattern with word boundaries
    if CRITICAL_KEYWORDS:
        KEYWORD_PATTERN = re.compile(r'\b(' + '|'.join(re.escape(word) for word in CRITICAL_KEYWORDS) + r')\b', re.IGNORECASE)
    else:
        KEYWORD_PATTERN = None
except (FileNotFoundError, yaml.YAMLError):
    KEYWORD_PATTERN = None


def present_result(text: str) -> str:
    """
    Applies color and formatting to the AI's final Markdown response
    to improve readability in the terminal.
    """
    # Color Headings (e.g., ### Analysis)
    text = re.sub(
        r"^(#+.*)$",
        f"{Colors.BOLD}{Colors.CYAN}\\1{Colors.RESET}",
        text,
        flags=re.MULTILINE
    )

    # Color Key Labels (e.g., **Claim:**)
    text = re.sub(
        r"(\*\*(?:Claim|Status|Evidence|Action|Reason|Finding|Problem|Impact|Recommendation):\*\*)",
        f"{Colors.YELLOW}\\1{Colors.RESET}",
        text
    )

    # Color specific success statuses
    text = re.sub(
        r"(Confirmed\.)",
        f"{Colors.GREEN}\\1{Colors.RESET}",
        text
    )

    # Color bullet points
    text = re.sub(
        r"(^\s*[\*\-]\s+)",
        f"{Colors.BLUE}\\1{Colors.RESET}",
        text,
        flags=re.MULTILINE
    )
    
    # Dim separators
    text = re.sub(
        r"(^[-=]{3,}\s*$)",
        f"{Colors.DIM}\\1{Colors.RESET}",
        text,
        flags=re.MULTILINE
    )

    return text


def highlight_critique(text: str) -> str:
    """
    Analyzes the critique text and highlights critical keywords for emphasis.
    """
    if not KEYWORD_PATTERN or not text:
        return text

    def replacer(match):
        """Wraps the matched keyword in color codes."""
        word = match.group(1)
        return f"{Colors.BOLD}{Colors.RED}{word}{Colors.RESET}"

    return KEYWORD_PATTERN.sub(replacer, text)