"""
This module will contain helper functions and classes for common clinical processing tasks
which will be used in medspaCy's matcher objects.
"""
import re
from typing import Union, Tuple, List

from spacy.tokens import Doc, Span, Token

from ..util import tuple_overlaps


def span_contains(
    span: Union[Doc, Span],
    target: str,
    regex: bool = True,
    case_insensitive: bool = True,
) -> bool:
    """
    Return True if a Span object contains a target phrase.

    Args:
        span: A spaCy Doc or Span, such as an entity in doc.ents
        target: A target phrase or iterable of phrases to check in span.text.lower().
        regex: Whether to search the span using a regular expression rather than
            a literal string. Default is True.
        case_insensitive: Whether the matching is case-insensitive. Default is True.
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


def get_token_for_char(
    doc: Doc, char_idx: int, resolve: str = "left"
) -> Union[Token, None]:
    """
    Get the token index that best matches a particular character index. Because regex find returns a character index and
    spaCy matches must align with token boundaries, each character index must be converted into a token index.

    Args:
        doc: The spaCy Doc to search in.
        char_idx: The character index to find the corresponding token for.
        resolve: The resolution type. "left" will snap character to the token index to the left which precede the
        `char_idx`. "right" will snap character to the token index to the right, which follows the `char_idx`.

    Returns:
        The token that best fits the character index based on the resolution type.
    """
    if char_idx < 0:
        raise ValueError("char_idx must be > 0")
    if char_idx > len(doc.text_with_ws):
        raise ValueError(
            "char_idx {0} is out of range for text with length {1}".format(
                char_idx, len(doc.text_with_ws)
            )
        )
    for i, token in enumerate(doc):
        if char_idx > token.idx:
            continue
        if char_idx == token.idx:
            return token
        if char_idx < token.idx:
            if resolve == "left":
                return doc[i - 1]
            elif resolve == "right":
                return doc[i]
            else:
                raise ValueError("resolve must be either 'left' or 'right'")
    # Otherwise, we've reached the end of the doc, so this must be the final token
    # If resolving to the left, return the final token
    # If resolving to the right, return None, meaning it should go to the end of the doc
    if resolve == "left":
        return doc[-1]
    if resolve == "right":
        return None


def prune_overlapping_matches(
    matches: List[Tuple[int, int, int]], strategy: str = "longest"
) -> List[Tuple[int, int, int]]:
    """
    Prunes overlapping matches from a list of spaCy match tuples (match_id, start, end).

    Args:
        matches: A list of match tuples of form (match_id, start, end).
        strategy: The pruning strategy to use. At this time, the only available option is "longest" and will keep the
            longest of any two overlapping spans. Other behavior will be added in a future update.

    Returns:
        The pruned list of matches.
    """
    if strategy != "longest":
        raise NotImplementedError(
            "No other filtering strategy has been implemented. Coming in a future update."
        )

    # Make a copy and sort
    unpruned = sorted(matches, key=lambda x: (x[1], x[2]))
    pruned = []
    num_matches = len(matches)
    if num_matches == 0:
        return matches
    curr_match = unpruned.pop(0)

    while True:
        if len(unpruned) == 0:
            pruned.append(curr_match)
            break
        next_match = unpruned.pop(0)

        # Check if they overlap
        if overlaps(curr_match, next_match):
            # Choose the larger span
            longer_span = max(curr_match, next_match, key=lambda x: (x[2] - x[1]))
            pruned.append(longer_span)
            if len(unpruned) == 0:
                break
            curr_match = unpruned.pop(0)
        else:
            pruned.append(curr_match)
            curr_match = next_match
    # Recursive base point
    if len(pruned) == num_matches:
        return pruned
    # Recursive function call
    else:
        return prune_overlapping_matches(pruned)


def overlaps(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> bool:
    """
    Checks whether two match Tuples out of spacy matchers overlap.

    Args:
        a: A match Tuple (match_id, start, end).
        b: A match Tuple (match_id, start, end).

    Returns:
        Whether the tuples overlap.
    """
    _, a_start, a_end = a
    _, b_start, b_end = b
    return tuple_overlaps((a_start, a_end), (b_start, b_end))


def matches_to_spans(
    doc: Doc, matches: List[Tuple[int, int, int]], set_label: bool = True
) -> List[Span]:
    """
    Converts all identified matches to spans.

    Args:
        doc: The spaCy doc corresponding to the matches.
        matches: The list of match Tuples (match_id, start, end).
        set_label: Whether to assign a label to the span based off the source rule. Default is True.

    Returns:
        A list of spacy spans corresponding to the input matches.
    """
    spans = []
    for (rule_id, start, end) in matches:
        if set_label:
            label = doc.vocab.strings[rule_id]
        else:
            label = None
        spans.append(Span(doc, start=start, end=end, label=label))
    return spans
