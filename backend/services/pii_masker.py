"""
PII masking for text that leaves the server.

Before any text is sent to an external AI service, personal details are
replaced with placeholders such as [EMAIL_1] or [PHONE_1]. The real values
stay in memory on this server, and are put back into the AI's answer
locally, so the reviewer still sees the real data.

What is masked: email addresses, phone numbers, payment card numbers (any
13-19 digit number), US SSNs, Indian PAN numbers and Aadhaar-style 12-digit
IDs.

NOT masked yet: people's names, places and codenames. That needs a
language model such as Microsoft Presidio and is a later step. Masking is
pattern-based, so it can miss unusual formats; it is a safety layer, not a
guarantee.
"""

import re
from typing import Callable, Dict, List, Tuple

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_AADHAAR = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
_PHONE = re.compile(r"(?<![\w.])\+?\(?\d[\d\s().-]{7,}\d(?!\w)")


def _is_card(value: str) -> bool:
    # Any 13-19 digit number is treated as a possible card number. A mistyped
    # card number is still sensitive, so no checksum is required.
    return 13 <= len(re.sub(r"\D", "", value)) <= 19


def _is_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return 10 <= len(digits) <= 15


# (placeholder kind, pattern, optional extra check on the matched text)
_RULES: List[Tuple[str, "re.Pattern[str]", Callable[[str], bool]]] = [
    ("EMAIL", _EMAIL, lambda v: True),
    ("CARD", _CARD, _is_card),
    ("ID", _SSN, lambda v: True),
    ("ID", _PAN, lambda v: True),
    ("ID", _AADHAAR, lambda v: True),
    ("PHONE", _PHONE, _is_phone),
]


class PiiMasker:
    """One masker per outgoing request. The same value always gets the same
    placeholder, so the AI sees consistent text and the answer can be restored."""

    def __init__(self) -> None:
        self._placeholder_for: Dict[Tuple[str, str], str] = {}
        self._original_for: Dict[str, str] = {}
        self._counts: Dict[str, int] = {}

    def _placeholder(self, kind: str, value: str) -> str:
        key = (kind, value)
        if key not in self._placeholder_for:
            self._counts[kind] = self._counts.get(kind, 0) + 1
            placeholder = f"[{kind}_{self._counts[kind]}]"
            self._placeholder_for[key] = placeholder
            self._original_for[placeholder] = value
        return self._placeholder_for[key]

    def mask(self, text: str) -> str:
        """Replace personal details in text with placeholders."""
        if not text:
            return text

        for kind, pattern, accept in _RULES:
            def replace(match, kind=kind, accept=accept):
                value = match.group(0)
                return self._placeholder(kind, value) if accept(value) else value

            text = pattern.sub(replace, text)
        return text

    def unmask(self, text: str) -> str:
        """Put the real values back (done locally, never sent anywhere)."""
        if not text:
            return text
        for placeholder, original in self._original_for.items():
            text = text.replace(placeholder, original)
        return text
