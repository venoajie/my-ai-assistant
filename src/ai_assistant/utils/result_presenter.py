# src/ai_assistant/result_presenter.py
import re
from .colors import Colors

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