NEWLINE_PATTERN = r"[\n\r]+[\s]*$"


def get_section_titles(doc):
    return [title for (title, _, _, _) in doc._.sections]


def get_section_headers(doc):
    return [header for (_, header, _, _) in doc._.sections]


def get_section_parents(doc):
    return [parent for (_, _, parent, _,) in doc._.sections]


def get_section_spans(doc):
    return [span for (_, _, _, span) in doc._.sections]


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
