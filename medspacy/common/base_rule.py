from typing import Union, Dict, List, Optional, Callable, Tuple, Any

from spacy.matcher import Matcher
from spacy.tokens import Doc


class BaseRule:
    """
    BaseRule is the basic class for the rules contained in the MedspacyMatcher class. It contains the basic structure
    for a rule to be used by the spaCy matchers or by the RegexMatcher class in order to produce match tuples for
    processing by a component such as the Sectionizer, ContextComponent or TargetMatcher
    """

    def __init__(
        self,
        literal: str,
        category: str,
        pattern: Optional[Union[str, List[Dict[str, str]]]] = None,
        on_match: Optional[
            Callable[[Matcher, Doc, int, List[Tuple[int, int, int]]], Any]
        ] = None,
        metadata: Optional[Dict[Any, Any]] = None,
    ):
        """
        Base class for medspaCy rules such as TargetRule and ConTextRule.

        Args:
            literal: The plaintext form of the pattern. Can be a human-readable form of a more complex pattern or, if
                `pattern` is None, the literal is used in a spaCy PhraseMatcher by the MedspacyMatcher.
            category: The category for the match. Corresponds to ent.label_ for entities.
            pattern: A list or string to use as a spaCy pattern rather than `literal`. If a list, will use spaCy
                token-based pattern matching to match using token attributes. If a string, will use medspaCy's
                RegexMatcher. If None, will use `literal` as the pattern for phrase matching. For more information, see
                https://spacy.io/usage/rule-based-matching.
            on_match: An optional callback function or other callable which takes 4 arguments: `(matcher, doc, i,
                matches)`. For more information, see https://spacy.io/usage/rule-based-matching#on_match
            metadata: Optional dictionary of any extra metadata.
        """
        self.literal = literal
        self.category = category
        self.pattern = pattern
        self.on_match = on_match
        self.metadata = metadata
