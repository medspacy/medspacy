"""
This module contains some simple functions that can be used as action or condition functions for postprocessing rules.
"""
from typing import Iterable, Union, Literal

from spacy.tokens import Span

from ..common.util import span_contains


def is_negated(span: Span) -> bool:
    """
    Returns whether a span is marked as negated.

    Args:
        span: The span to check.

    Returns:
        Whether the specified span has span._.is_negated set to True.
    """
    return span._.is_negated


def is_uncertain(span: Span) -> bool:
    """
    Returns whether a span is marked as uncertain.

    Args:
        span: The span to check.

    Returns:
        Whether the specified span has span._.is_uncertain set to True.
    """
    return span._.is_uncertain


def is_historical(span: Span) -> bool:
    """
    Returns whether a span is marked as historical.

    Args:
        span: The span to check.

    Returns:
        Whether the specified span has span._.is_historical set to True.
    """
    return span._.is_historical


def is_hypothetical(span: Span) -> bool:
    """
    Returns whether a span is marked as hypothetical.

    Args:
        span: The span to check.

    Returns:
        Whether the specified span has span._.is_hypothetical set to True.
    """
    return span._.is_hypothetical


def is_family(span: Span) -> bool:
    """
    Returns whether a span is marked as family.

    Args:
        span: The span to check.

    Returns:
        Whether the specified span has span._.is_family set to True.
    """
    return span._.is_family


def is_modified_by_category(span: Span, category: str) -> bool:
    """
    Returns whether a span is modified by a ConTextModifier of that type.

    Args:
        span: The span to check.
        category: The category to check whether a ConTextModifier of that type modifies the span.

    Returns:
        Whether the specified span has the specified modifier type.
    """
    for modifier in span._.modifiers:
        if modifier.category.upper() == category.upper():
            return True
    return False


def is_modified_by_text(
    span: Span, target: Union[str, Iterable[str]], regex: bool = True
) -> bool:
    """
    Returns whether a span is modified by a ConTextModifier with the specified text.

    Args:
        span: The span to check.
        target: The category to check whether a ConTextModifier with this text modifies the span.
        regex: If the `target` specified is a regex pattern. Default is True.

    Returns:
        Whether the specified span has the specified modifier type.
    """
    for modifier in span._.modifiers:
        if span_contains(modifier.span, target, regex):
            return True
    return False


def is_preceded_by(
    ent: Span, target: Union[str, Iterable[str]], window: int = 1
) -> bool:
    """
    Checks if an entity is preceded by a target word within a certain window. If any phrases in target are more than one
    token long, this may not capture it if window is smaller than the number of tokens. Case-insensitive.

    Args:
        ent: The span to check.
        target: A string or a collection of strings that will be searched for in the text preceding `ent`.
        window: The number of tokens to search for `target` preceding `ent`. Default is 1.

    Returns:
        Whether the entity specified is preceded by a target.
    """
    preceding_span = ent.doc[ent.start - window : ent.start]
    preceding_string = " ".join([token.text.lower() for token in preceding_span])
    if isinstance(target, str):
        return target.lower() in preceding_string
    for string in target:
        if string.lower() in preceding_string:
            return True
    return False


def is_followed_by(
    ent: Span, target: Union[str, Iterable[str]], window: int = 1
) -> bool:
    """
    Checks if an entity is followed by a target word within a certain window. If any phrases in target are more than one
    token long, this may not capture it if window is smaller than the number of tokens. Case-insensitive.

    Args:
        ent: The span to check.
        target: A string or a collection of strings that will be searched for in the text following `ent`.
        window: The number of tokens to search for `target` following `ent`. Default is 1.

    Returns:
        Whether the entity specified is followed by a target.
    """
    following_span = ent.doc[ent.end : ent.end + window]
    following_string = " ".join([token.text.lower() for token in following_span])
    if isinstance(target, str):
        return target.lower() in following_string
    for string in target:
        if string.lower() in following_string:
            return True
    return False


def ent_contains(
    ent: Span, target: Union[str, Iterable[str]], regex: bool = True
) -> bool:
    """
    Check if an entity occurs in the same sentence as another span of text. Case-insensitive.

    Args:
        ent: The span to check.
        target: A string or a collection of strings that will be searched inside `ent`.
        regex: If the `target` specified is a regex pattern. Default is True.

    Returns:
        Whether the target is contained in the ent.
    """
    return span_contains(ent, target, regex)


def sentence_contains(ent: Span, target: Union[str, Iterable[str]], regex=True) -> bool:
    """
    Check if an entity occurs in the same sentence as another span of text.

    Args:
        ent: The span to check.
        target: A string or a collection of strings that will be searched for in the text of the sentence containing
            `ent`.
        regex: If the `target` specified is a regex pattern. Default is True.
    """
    return span_contains(ent.sent, target, regex)


def remove_ent(
    ent: Span,
    i: int,
    input_type: Literal["ents", "group"] = "ents",
    span_group_name: str = "medspacy_spans",
):
    """
    Remove an entity at position [i] from doc.ents.

    Args:
        ent: The entity to remove.
        i: The index of `ent` in its source list.
        input_type: The source of the entity, either "ents" or "group".
        span_group_name: If `input_type` is "group", the name of the span group.
    """
    if input_type == "ents":
        ent.doc.ents = ent.doc.ents[:i] + ent.doc.ents[i + 1 :]
    elif input_type == "group":
        ent.doc.spans[span_group_name] = (
            ent.doc.spans[span_group_name][:i] + ent.doc.spans[span_group_name][i + 1 :]
        )


def set_label(
    ent,
    i,
    input_type: Literal["ents", "group"] = "ents",
    span_group_name: str = "medspacy_spans",
    **kwargs
):
    """
    Creates a copy of the entity with a new label.

    WARNING: This is not fully safe, as spaCy does not allow modifying the label of a span. Instead, this creates a new
    copy and attempts to copy existing attributes, but this is not totally reliable.

    Args:
        ent: The entity to MODIFY.
        i: The index of `ent` in its source list.
        input_type: The source of the entity, either "ents" or "group".
        span_group_name: If `input_type` is "group", the name of the span group.
    """
    from spacy.tokens import Span

    new_ent = Span(ent.doc, ent.start, ent.end, label=kwargs["label"])
    # Copy any additional attributes
    # NOTE: This may not be complete and should be used with caution
    for (attr, values) in ent._.__dict__["_extensions"].items():
        setattr(new_ent._, attr, values[0])
    if input_type == "ents":
        if len(ent.doc.ents) == 1:
            ent.doc.ents = (new_ent,)
        else:
            ent.doc.ents = ent.doc.ents[:i] + (new_ent,) + ent.doc.ents[i + 1 :]
    else:
        if len(ent.doc.spans[span_group_name] == 1):
            ent.doc.spans[span_group_name] = (new_ent,)
        else:
            ent.doc.spans[span_group_name] = (
                ent.doc.spans[span_group_name][:i]
                + (new_ent,)
                + ent.doc.spans[span_group_name][i + 1 :]
            )


def set_negated(ent, i, value=True):
    """Set the value of ent._.is_negated to value."""
    ent._.is_negated = value


def set_uncertain(ent, i, value=True):
    """Set the value of ent._.is_uncertain to value."""
    ent._.is_uncertain = value


def set_historical(ent, i, value=True):
    """Set the value of ent._.is_historical to value."""
    ent._.is_historical = value


def set_hypothetical(ent, i, value=True):
    """Set the value of ent._.is_hypothetical to value."""
    ent._.is_hypothetical = value


def set_family(ent, i, value=True):
    "Set the value of ent._.is_family to value."
    ent._.is_hypothetical = value
