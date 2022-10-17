"""
This module will contain helper functions and classes for common clinical processing tasks
which will be used in medspaCy's context implementation.
"""
from spacy.tokens import Span


def is_modified_by(span: Span, modifier_label: str) -> bool:
    """
    Check whether a span has a modifier of a specific type.

    Args:
        span: The span to examine.
        modifier_label: The type of modifier to check for.

    Returns:
        Whether there is a modifier of `modifier_label` that modifies `span`.
    """
    for modifier in span._.modifiers:
        if modifier.category.upper() == modifier_label.upper():
            return True
    return False
