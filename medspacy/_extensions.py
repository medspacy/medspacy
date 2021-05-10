"""This module will set extension attributes and methods for medspaCy. Examples include custom methods like span._.window()"""
from spacy.tokens import Doc, Span, Token
from .common.util import span_contains
# from .io.doc_consumer import ALLOWED_DATA_TYPES

ALLOWED_DATA_TYPES = ("ent", "section", "context", "doc")

def set_extensions():
    "Set custom medspaCy extensions for Token, Span, and Doc classes."
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

def get_window_span(span, n=1, left=True, right=True):
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
        start = max((span.start-n, 0))
    else:
        start = span.start
    if right:
        end = min((span.end+n, len(span.doc)))
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

def get_span_literal(span):
    """Get the literal value from an entity's TargetRule, which is set when an entity is extracted by TargetMatcher.
    If the span does not have a TargetRule, it returns the lower-cased text.
    """
    target_rule = span._.target_rule
    if target_rule is None:
        return span.lower_
    return target_rule.literal

def any_context_attribute(span):
    "Return True if any of the ConText assertion attributes (is_negated, is_historical, etc.) is True."
    return any(span._.context_attributes.values())

def get_section_title_spans(doc):
    return [section.title_span for section in doc._.sections]

def get_section_categories(doc):
    return [section.category for section in doc._.sections]

def get_section_parents(doc):
    return [section.parent for section in doc._.sections]

def get_section_spans(doc):
    return [section.section_span for section in doc._.sections]

def get_section_body_spans(doc):
    return [section.body_span for section in doc._.sections]

def get_section_span_token(token):
    if token._.section is None:
        return None
    return token._.section.section_span

def get_section_category_token(token):
    if token._.section is None:
        return None
    return token._.section.category

def get_section_title_span_token(token):
    if token._.section is None:
        return None
    return token._.section.title_span

def get_section_body_span_token(token):
    if token._.section is None:
        return None
    return token._.section.body_span

def get_section_parent_token(token):
    if token._.section is None:
        return None
    return token._.section.parent

def get_section_rule_token(token):
    if token._.section is None:
        return None
    return token._.section.rule

def get_data(doc, dtype=None, attrs=None ,as_rows=False):
    if doc._.data is None:
        import warnings
        warnings.warn("doc._.data is None, which might mean that you haven't processed your doc with a DocConsumer yet.\n"
                         "Make sure you've processed a doc by either calling doc_consumer(doc) or nlp.add_pipe(doc_consumer)",
                      RuntimeWarning
                      )
        return None

    if dtype is None:
        if as_rows is True:
            raise ValueError("as_rows can only be True if dtype is dtype is not None.")
        return doc._.data
    if dtype in ALLOWED_DATA_TYPES:
        data = doc._.data.get(dtype, list())
        if attrs is not None:
            from collections import OrderedDict
            selected_data = OrderedDict()
            for key in attrs:
                if key not in data:
                    raise ValueError("Invalid attr value:", key)
                selected_data[key] = data[key]
            data = selected_data
        if as_rows:
            data = data_to_rows(data)
        return data
    else:
        raise ValueError("Invalid data type requested: {0}. Must be one of {1}".format(dtype, ALLOWED_DATA_TYPES))

def data_to_rows(data):
    """Unzip column-wise data from doc._.data into rows"""
    col_data = [data[key] for key in data.keys()]
    row_data = list(zip(*col_data))
    return row_data

def to_dataframe(doc, data_type="ent"):
    if data_type not in ALLOWED_DATA_TYPES:
        raise ValueError("Invalid data type requested: {0}. Must be one of {1}".format(data_type, ALLOWED_DATA_TYPES))
    import pandas as pd
    doc_data = pd.DataFrame(data=doc._.get_data(data_type))
    return doc_data



_token_extensions = {
   "window": {"method": get_window_token},
    "section": {"default": None},
   "section_span": {"getter": get_section_span_token},
   "section_category": {"getter": get_section_category_token},
   "section_title": {"getter": get_section_title_span_token},
   "section_body": {"getter": get_section_body_span_token},
   "section_parent": {"getter": get_section_parent_token},
   "section_rule": {"getter": get_section_rule_token},
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
    "section": {"getter":lambda x: x[0]._.section},
    "section_span": {"getter":lambda x: x[0]._.section_span},
    "section_category": {"getter":lambda x: x[0]._.section_category},
    "section_title": {"getter":lambda x: x[0]._.section_title},
    "section_body": {"getter":lambda x: x[0]._.section_body},
    "section_parent": {"getter":lambda x: x[0]._.section_parent},
    "section_rule": {"getter":lambda x: x[0]._.section_rule},
    "contains": {"method": span_contains},
    "target_rule": {"default": None},
    "literal": {"getter": get_span_literal},
    **_context_attributes

}

_doc_extensions = {
    "sections": {"default": list()},
    "section_titles": {"getter": get_section_title_spans},
    "section_categories": {"getter": get_section_categories},
    "section_spans": {"getter": get_section_spans},
    "section_parents": {"getter": get_section_parents},
    "section_bodies": {"getter": get_section_body_spans},
    "get_data": {"method": get_data},
    "data": {"default": None},
    "ent_data": {"getter": lambda doc: get_data(doc, "ent")},
    "section_data": {"getter": lambda doc: get_data(doc, "section")},
    "doc_data": {"getter": lambda doc: get_data(doc, "doc")},
    "context_data": {"getter": lambda doc: get_data(doc, "context")},
    "to_dataframe": {"method": to_dataframe}
}



