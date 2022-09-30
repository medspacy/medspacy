import re
import warnings
from typing import Iterable, Callable, Optional, List, Tuple, Any

from spacy import Vocab
from spacy.matcher import Matcher
from spacy.tokens import Doc

from .util import get_token_for_char


# we warn here but i'm not sure it's necessary.
# warnings.filterwarnings("once", "You are using a TargetRule with a regex pattern.*")


class RegexMatcher:
    """
    The RegexMatcher is an alternative to spaCy's native Matcher and PhraseMatcher classes and allows matching based on
    typical regular expressions over the underlying doc text rather than spacy token attributes.

    This can be useful for allowing more traditional text matching methods, but can lead to issues if the matched spans
    in the text do not line up with spacy token boundaries. In this case, the RegexMatcher will by default resolve to
    the nearest token  boundaries by expanding to the left and right. This behavior can be configured using
    `resolve_start` and `resolve_end`. To avoid this, consider using a list of dicts, such as in a spacy Matcher.
    For more information, see: https://spacy.io/usage/rule-based-matching

    Examples of resolve_start/resolve_end:
    In the string 'SERVICE: Radiology' the pattern 'ICE: Rad' would match in the middle of the tokens
    'SERVICE' and 'RADIOLOGY'. SpaCy would normally return None. The RegexMatcher will expand in the following ways:
    resolve_start='left': The resulting span will start at 'SERVICE' -> 'SERVICE: Radiology'
    resolve_start='right': The resulting span will start at ':' -> ': Radiology'
    resolve_end='left': The resulting span will end at ':': -> 'SERVICE:'
    resolve_end='right': The resulting span will end at 'RADIOLOGY' -> 'SERVICE: Radiology'

    """

    def __init__(
        self,
        vocab: Vocab,
        flags: re.RegexFlag = re.IGNORECASE,
        resolve_start: str = "left",
        resolve_end: str = "right",
    ):
        """
        Creates a new RegexMatcher.

        Args:
            vocab: A spaCy model vocabulary
            flags: Regular expression flag. Default re.IGNORECASE
            resolve_start: How to resolve if the start character index of a match does not align with spacy token
                boundaries. If 'left', will find the nearest token boundary to the left of the unmatched character
                index, leading to a longer than expected span. If 'right', will find the nearest token boundary to the
                right of the unmatched character index, leading to a shorter than expected span.  Default 'left'.
            resolve_end: How to resolve if the end character index of a match does not align with spacy token
                boundaries. If 'left', will find the nearest token boundary to the left of the unmatched character
                index, leading to a shorter than expected span. If 'right', will find the nearest token boundary to the
                right of the unmatched character index, leading to a longer than expected span. Default 'right'.
        """
        self.vocab = vocab
        self.flags = flags
        self.resolve_start = resolve_start
        self.resolve_end = resolve_end
        self._patterns = {}
        self._callbacks = {}
        self.labels = set()
        self._rule_item_mapping = dict()

    def add(
        self,
        match_id: str,
        regex_rules: Iterable[str],
        on_match: Optional[
            Callable[[Matcher, Doc, int, List[Tuple[int, int, int]]], Any]
        ] = None,
    ):
        """
        Add a rule with one or more regex patterns to one match id.

        Args:
            match_id: The name of the pattern.
            regex_rules: The list of regex strings to associate with `match_id`.
            on_match: An optional callback function or other callable which takes 4 arguments: `(matcher, doc, i,
                matches)`. For more information, see https://spacy.io/usage/rule-based-matching#on_match
        """
        # i am not sure if these warnings are more annoying than useful.
        # warnings.warn(
        #     "You are using a TargetRule with a regex pattern, which is not "
        #     "natively supported in spacy and may lead to unexpected match spans. "
        #     "Consider using a list of dicts pattern instead. "
        #     "See https://spacy.io/usage/rule-based-matching",
        #     RuntimeWarning,
        # )
        if match_id not in self.vocab:
            self.vocab.strings.add(match_id)
        self._patterns.setdefault(self.vocab.strings[match_id], [])
        for pattern in regex_rules:
            self._patterns[self.vocab.strings[match_id]].append(
                re.compile(pattern, flags=self.flags)
            )
            self._callbacks[self.vocab.strings[match_id]] = on_match

    def get(self, key):
        return self._patterns.get(self.vocab.strings[key], [])

    def __call__(self, doc: Doc) -> List[Tuple[int, int, int]]:
        """
        Call the RegexMatcher on a spaCy Doc.

        Args:
            doc: The spaCy doc to process.

        Returns:
            The list of match tuples (match_id, start, end).
        """
        matches = []
        for (match_id, patterns) in self._patterns.items():
            for pattern in patterns:
                on_match = self._callbacks[match_id]
                for re_match in pattern.finditer(doc.text_with_ws):
                    span = doc.char_span(re_match.start(), re_match.end())
                    if span is None:
                        start = get_token_for_char(
                            doc, re_match.start(), resolve=self.resolve_start
                        )
                        end = get_token_for_char(
                            doc, re_match.end(), resolve=self.resolve_end
                        )
                        if end is None:
                            end_index = len(doc)
                        else:
                            end_index = end.i
                        span = doc[start.i : end_index]
                    # If it's an empty span, then that means that the token resolution
                    # must have resulted in no tokens being included.
                    # Don't add the match
                    if len(span):
                        match = (match_id, span.start, span.end)
                        matches.append(match)
                    # If a callback function was defined,
                    # call it according to the spaCy API:
                    # https://spacy.io/usage/rule-based-matching#on_match
                    if on_match is not None:
                        on_match(self, doc, len(matches) - 1, matches)

        return matches
