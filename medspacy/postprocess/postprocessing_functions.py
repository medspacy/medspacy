"""This module contains functions to be used both as action and condition functions
for postprocessing patterns.
"""

# Condition functions

def is_negated(span):
    """Return True if a span is marked as negated by cycontext."""
    return span._.is_negated

def is_uncertain(span):
    """Return True if a span is marked as uncertain by cycontext."""
    return span._.is_uncertain

def is_historical(span):
    """Return True if a span is marked as historical by cycontext."""
    return span._.is_historical

def is_hypothetical(span):
    """Return True if a span is marked as hypothetical by cycontext."""
    return span._.is_hypothetical

def is_family(span):
    """Return True if a span is marked as family by cycontext."""
    return span._.is_family

def is_modified_by_category(span, category):
    """Returns True if a span is modified by a cycontext ConTextModifier
    modifier with a certain category. Case insensitive.
    """
    for modifier in span._.modifiers:
        if modifier.category.upper() == category.upper():
            return True
    return False

def is_modified_by_text(span, target, regex=True):
    """Returns True if a span is modified by a cycontext TabObject
    modifier with a certain text.
    """
    for modifier in span._.modifiers:
        if span_contains(modifier.span, target, regex):
            return True
    return False

def is_preceded_by(ent, target, window=1):
    """Check if an entity is preceded by a target word within a certain window.
    Case-insensitive.
    If any phrases in target are more than one token long, this may not capture it
    if window is smaller than the number of tokens.
    ent (Span):  A spaCy Span
    target (str or iterable): Either a single string or iterable of strings.
        If an iterable, will return True if any of the strings are in the window
        preceding ent.
    """
    preceding_span = ent.doc[ent.start - window: ent.start]
    preceding_string = " ".join([token.lower_ for token in preceding_span])
    if isinstance(target, str):
        return target.lower() in preceding_string
    for string in target:
        if string.lower() in preceding_string:
            return True
    return False


def is_followed_by(ent, target, window=1):
    """Check if an entity is followed by a target word within a certain window.
    Case-insensitive.
    If any phrases in target are more than one token long, this may not capture it
    if window is smaller than the number of tokens.
    ent (Span):  A spaCy Span
    target (str or iterable): Either a single string or iterable of strings.
        If an iterable, will return True if any of the strings are in the window
        following ent.
    """
    following_span = ent.doc[ent.end: ent.end+window]
    following_string = " ".join([token.lower_ for token in following_span])
    if isinstance(target, str):
        return target.lower() in following_string
    for string in target:
        if string.lower() in following_string:
            return True
    return False

def span_contains(span, target, regex=True):
    """Return True if a Span object contains a target phrase.
    Case insensitive.
    span: A spaCy Span, such as an entity in doc.ents
    target: A target phrase or iterable of phrases to check in span.lower_.
    regex (bool): Whether to search the span using a regular expression rather than
        a literal string. Default True.
    """
    if regex is True:
        import re
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

def ent_contains(ent, target, regex=True):
    """Check if an entity occurs in the same sentence as another span of text.
    ent (Span): A spaCy Span
    target (str or iterable): Either a single string or iterable of strings.
        If an iterable, will return True if any of the strings are a substring
        of ent.sent.
    Case insensitive.
    """
    return span_contains(ent, target, regex)


def sentence_contains(ent, target, regex=True):
    """Check if an entity occurs in the same sentence as another span of text.
    ent (Span): A spaCy Span
    target (str or iterable): Either a single string or iterable of strings.
        If an iterable, will return True if any of the strings are a substring
        of ent.sent.
    Case insensitive.
    """
    return span_contains(ent.sent, target, regex)

# Action funcs

def remove_ent(ent, i):
    """Remove an entity at position [i] from doc.ents."""
    ent.doc.ents = ent.doc.ents[:i] + ent.doc.ents[i+1:]

def set_label(ent, i, label):
    """Create a copy of the entity with a new label.
    WARNING: This is not fully safe, as spaCy does not allow modifying the label
    of a span. Instead this creates a new copy and attempts to copy existing
    attributes, but this is not totally reliable.
    """
    from spacy.tokens import Span
    new_ent = Span(ent.doc, ent.start, ent.end, label=label)
    # Copy any additional attributes
    # NOTE: This may not be complete and should be used with caution
    for (attr, values) in ent._.__dict__["_extensions"].items():
        setattr(new_ent._, attr, values[0])
    if len(ent.doc.ents) == 1:
        ent.doc.ents = (new_ent,)
    else:
        try:
            ent.doc.ents = ent.doc.ents[:i] + (new_ent,) + ent.doc.ents[i+1:]
        except ValueError: # Overlaps with another entity - debug later
            pass

def set_negated(ent, i, value=True):
    "Set the value of ent._.is_negated to value."
    ent._.is_negated = value

def set_uncertain(ent, i, value=True):
    "Set the value of ent._.is_uncertain to value."
    ent._.is_uncertain = value

def set_historical(ent, i, value=True):
    "Set the value of ent._.is_historical to value."
    ent._.is_historical = value

def set_hypothetical(ent, i, value=True):
    "Set the value of ent._.is_hypothetical to value."
    ent._.is_hypothetical = value

def set_family(ent, i, value=True):
    "Set the value of ent._.is_family to value."
    ent._.is_hypothetical = value
