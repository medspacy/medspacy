"""This module will set extension attributes and methods for medspaCy. Examples include custom methods like span._.window()"""
from spacy.tokens import Doc, Span, Token

def set_extensions():
    set_token_extensions()
    set_span_extensions()
    set_doc_extensions()

def set_token_extensions():
    for attr, attr_info in _token_extensions.items():
        try:
            Token.set_extension(attr, **attr_info)
        except ValueError as e: # If the attribute has already set, this will raise an error
            pass

def set_span_extensions():
    for attr, attr_info in _span_extensions.items():
        try:
            Span.set_extension(attr, **attr_info)
        except ValueError as e: # If the attribute has already set, this will raise an error
            pass

def set_doc_extensions():
    for attr, attr_info in _doc_extensions.items():
        try:
            Doc.set_extension(attr, **attr_info)
        except ValueError as e: # If the attribute has already set, this will raise an error
            pass

def get_extensions():
    "Get a list of medspaCy extensions for Token, Span, and Doc classes."
    return {
        "Token": get_token_extensions(),
        "Span": get_span_extensions(),
        "Doc": get_doc_extensions()
    }

def get_token_extensions():
    return _token_extensions

def get_span_extensions():
    return _span_extensions

def get_doc_extensions():
    return _doc_extensions

def get_window_token(token, n=1, left=True, right=True):
    """Get a Span of a window of text containing a token.
    Args:
        n (int): Number of tokens on each side of token to return.
            Default 1.
        left (bool): Whether to include the span preceding token.
            Default True.
        right (bool): Whether to include the span following token.
            Default True.
    Returns:
        a spaCy Span
    """
    if left:
        start = max((token.i-n, 0))
    else:
        start = token.i
    if right:
        end = min((token.i+n+1, len(token.doc)))
    else:
        end = token.i+1
    return token.doc[start:end]

def get_window_span(span, window=1, left=True, right=True):
    """Get a Span of a window of text containing a span.
    Args:
        n (int): Number of tokens on each side of a span to return.
            Default 1.
        left (bool): Whether to include the span precedinga span.
            Default True.
        right (bool): Whether to include the span following a span.
            Default True.
    Returns:
        a spaCy Span
    """
    if left:
        start = max((span.start-window, 0))
    else:
        start = span.start
    if right:
        end = min((span.end+window, len(span.doc)))
    else:
        end = span.end
    return span.doc[start:end]

def get_context_attributes(span):
    """Return a dict of all ConText assertion attributes (is_negated, is_historical, etc.)
    and their values.
    """
    attr_dict = dict()
    for attr in _context_attributes:
        attr_dict[attr] = span._.get(attr)
    return attr_dict

def any_context_attribute(span):
    "Return True if any of the ConText assertion attributes (is_negated, is_historical, etc.) is True."
    return any(span._.context_attributes.values())

def get_section_titles(doc):
    return [section.title for section in doc._.sections]

def get_section_headers(doc):
    return [section.header for section in doc._.sections]

def get_section_parents(doc):
    return [section.parent for section in doc._.sections]

def get_section_spans(doc):
    return [section.span for section in doc._.sections]

_token_extensions = {
   "window": {"method": get_window_token},
   "section_span": {"default": None},
   "section_title": {"default": None},
   "section_header": {"default": None},
   "section_parent": {"default": None},
}

_context_attributes = {
    "is_negated": {"default": False},
    "is_historical": {"default": False},
    "is_hypothetical": {"default": False},
    "is_family": {"default": False},
    "is_uncertain": {"default": False},
}


_span_extensions = {
    "window": {"method": get_window_span},
    "context_attributes": {"getter": get_context_attributes},
    "any_context_attributes": {"getter": any_context_attribute},
    "section_span": {"getter":lambda x: x[0]._.section_span},
    "section_title": {"getter":lambda x: x[0]._.section_title},
    "section_header": {"getter":lambda x: x[0]._.section_header},
    "section_parent": {"getter":lambda x: x[0]._.section_parent},
    **_context_attributes

}

_doc_extensions = {
    "window": {"method": get_window_span},
    "sections": {"default": list()},
    "section_titles": {"getter": get_section_titles},
    "section_headers": {"getter": get_section_headers},
    "section_spans": {"getter": get_section_spans},
    "section_parents": {"getter": get_section_parents},
}





