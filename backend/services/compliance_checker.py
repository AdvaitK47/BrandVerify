import re

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")

def check_text(text: str, rules: dict) -> list[dict]:
    findings, normalized = [], text.casefold()
    for phrase in rules.get("required_phrases", []):
        if phrase.casefold() not in normalized:
            findings.append({"rule": f"Required phrase: {phrase}", "status": "fail",
                "evidence": "Required phrase not found.", "suggestion": f'Add "{phrase}".',
                "source": "exact_phrase_check"})
    for phrase in rules.get("prohibited_phrases", []):
        if phrase.casefold() in normalized:
            findings.append({"rule": f"Prohibited phrase: {phrase}", "status": "review_required",
                "evidence": f'Matched text: "{phrase}"', "suggestion": "Revise the phrase and ask a reviewer to confirm.",
                "source": "exact_phrase_check"})
    for match in EMAIL_RE.finditer(text):
        findings.append({"rule": "Possible email / privacy risk", "status": "review_required",
            "evidence": match.group(0), "suggestion": "Confirm publishing this email is authorized.",
            "source": "privacy_pattern_check"})
    for match in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if 8 <= len(digits) <= 15:
            findings.append({"rule": "Possible phone / privacy risk", "status": "review_required",
                "evidence": match.group(0), "suggestion": "Confirm publishing this number is authorized.",
                "source": "privacy_pattern_check"})
    if not findings:
        findings.append({"rule": "Implemented text checks", "status": "pass",
            "evidence": "No issue detected by exact phrase and basic privacy checks.",
            "suggestion": None, "source": "deterministic_checks"})
    return findings

def check_colors(colors: list[str], rules: dict) -> list[dict]:
    approved = {c.upper() for c in rules.get("approved_colors", [])}
    if not colors:
        return [{"rule": "Approved color palette", "status": "review_required",
            "evidence": "No detected colors supplied.", "suggestion": "Run a visual detector or review manually.",
            "source": "color_check"}]
    findings = []
    for color in colors:
        if approved and color.upper() not in approved:
            findings.append({"rule": "Color outside exact approved palette", "status": "review_required",
                "evidence": color, "suggestion": "Replace with an approved color or use perceptual Delta-E matching.",
                "source": "exact_color_check"})
    if not findings:
        findings.append({"rule": "Approved color palette",
            "status": "pass" if approved else "review_required",
            "evidence": "Colors match exact palette." if approved else "No approved palette configured.",
            "suggestion": None if approved else "Admin should add approved colors.",
            "source": "exact_color_check"})
    return findings

def overall_status(findings: list[dict]) -> str:
    statuses = {x.get("status") for x in findings}
    if "fail" in statuses: return "fail"
    if "review_required" in statuses: return "review_required"
    return "pass"
