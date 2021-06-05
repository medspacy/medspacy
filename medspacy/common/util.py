"""Module for utility functions contained by multiple components of medspaCy."""
import re

def span_contains(span, target, regex=True, case_insensitive=False):
    """Return True if a Span object contains a target phrase.
    Case insensitive.
    span: A spaCy Span, such as an entity in doc.ents
    target: A target phrase or iterable of phrases to check in span.text.lower().
    regex (bool): Whether to search the span using a regular expression rather than
        a literal string. Default True.
    """
    if regex is True:
        if case_insensitive:
            func = lambda x: re.search(x, span.text, flags=re.IGNORECASE) is not None
        else:
            func = lambda x: re.search(x, span.text) is not None
    else:
        if case_insensitive:
            func = lambda x: x.lower() in span.text.lower()
        else:
            func = lambda x: x in span.text

    if isinstance(target, str):
        return func(target)

    # If it's an iterable, check if any of the strings are in sent
    for string in target:
        if func(string):
            return True
    return False
