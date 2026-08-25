"""Back-compat imports. The checklist agent is the real checker."""

from kill_scam.agent import classify_message, parse_verdict

__all__ = ["classify_message", "parse_verdict"]
