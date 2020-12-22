"""Module for utility functions contained by multiple components of medspaCy."""
import re

def span_contains(span, target, regex=True):
    """Return True if a Span object contains a target phrase.
    Case insensitive.
    span: A spaCy Span, such as an entity in doc.ents
    target: A target phrase or iterable of phrases to check in span.lower_.
    regex (bool): Whether to search the span using a regular expression rather than
        a literal string. Default True.
    """
    if regex is True:
        func = lambda x: re.search(x, span.lower_, re.IGNORECASE) is not None
    else:
        func = lambda x: x.lower() in span.lower_

    if isinstance(target, str):
        return func(target)

    # If it's an iterable, check if any of the strings are in sent
    for string in target:
        if func(string):
            return True
    return False