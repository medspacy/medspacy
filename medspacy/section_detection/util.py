import re

from spacy.tokens import Doc

NEWLINE_PATTERN = r"[\n\r]+[\s]*$"


def is_start_line(idx: int, doc: Doc, pattern: re.Pattern) -> bool:
    """
    Check whether the token at idx occurs at the start of the line.

    Args:
        idx: The token index to check.
        doc: The doc to check in.
        pattern: The newline pattern to check with.

    Returns:
        Whether the token occurs at the start of a line.
    """
    # If it's the start of the doc, return True
    if idx == 0:
        return True
    # Otherwise, check if the preceding token ends with newlines
    preceding_text = doc[idx - 1].text_with_ws
    return pattern.search(preceding_text) is not None


def is_end_line(idx: int, doc: Doc, pattern: re.Pattern) -> bool:
    """
    Check whether the token at idx occurs at the end of the line.

    Args:
        idx: The token index to check.
        doc: The doc to check in.
        pattern: The newline pattern to check with.

    Returns:
        Whether the token occurs at the end of a line.
    """
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
