NEWLINE_PATTERN = r"[\n\r]+[\s]*$"

def is_start_line(idx, doc, pattern):
    # If it's the start of the doc, return True
    if idx == 0:
        return True
    # Otherwise, check if the preceding token ends with newlines
    preceding_text = doc[idx - 1].text_with_ws
    return pattern.search(preceding_text) is not None


def is_end_line(idx, doc, pattern):
    # If it's the end of the doc, return True
    if idx == len(doc) - 1:
        return True

    # Check if either the token has trailing newlines,
    # or if the next token is a newline
    text = doc[idx].text_with_ws
    if pattern.search(text) is not None:
        return True
    following_text = doc[idx + 1].text_with_ws
    return pattern.search(following_text) is not None

def section_patterns_to_rules(patterns):
    """Convert a list of dictionary-based patterns of the old Sectionizer API
    to a list of SectionRules.
    """
    _ALLOWED_KEYS = {"category", "metadata", "parents", "parent_required"}
    from .section_rule import SectionRule

    rules = []
    for pattern in patterns:
        refactored = {}
        if isinstance(pattern["pattern"], str):
            refactored["literal"] = pattern["pattern"]
            refactored["pattern"] = None
        elif isinstance(pattern["pattern"], list):
            refactored["literal"] = str(pattern["pattern"])
            refactored["pattern"] = pattern["pattern"]

        refactored["category"] = pattern["section_title"]
        for key in _ALLOWED_KEYS:
            if key in pattern:
                refactored[key] = pattern[key]
        rule = SectionRule(**refactored)
        rules.append(rule)
    return rules
