NEWLINE_PATTERN = r"[\n\r]+[\s]*$"


def get_section_categories(doc):
    return [section.category for section in doc._.sections]


def get_section_title_spans(doc):
    return [section.title_span for section in doc._.sections]


def get_section_body_spans(doc):
    return [section.body_span for section in doc._.sections]


def get_section_spans(doc):
    return [section.section_span for section in doc._.sections]


def get_section_parents(doc):
    return [section.parent for section in doc._.sections]


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
