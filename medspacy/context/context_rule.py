from __future__ import annotations
import json
from typing import Optional, Callable, Union, List, Dict, Tuple, Any, Iterable, Set

from spacy.matcher import Matcher
from spacy.tokens import Doc, Span

from ..common.base_rule import BaseRule

# import warnings
#
# warnings.simplefilter("always")


class ConTextRule(BaseRule):
    """
    A ConTextRule defines a ConText modifier. ConTextRules are rules which define which spans are extracted as modifiers
    and how they behave, such as the phrase to be matched, the category/semantic class, the direction of the modifier in
    the text, and what types of target spans can be modified.
    """

    _ALLOWED_DIRECTIONS = (
        "FORWARD",
        "BACKWARD",
        "BIDIRECTIONAL",
        "TERMINATE",
        "PSEUDO",
    )
    _ALLOWED_KEYS = {
        "literal",
        "direction",
        "pattern",
        "category",
        "metadata",
        "allowed_types",
        "excluded_types",
        "max_targets",
        "max_scope",
    }

    def __init__(
        self,
        literal: str,
        category: str,
        pattern: Optional[Union[str, List[Dict[str, str]]]] = None,
        direction: str = "BIDIRECTIONAL",
        on_match: Optional[
            Callable[[Matcher, Doc, int, List[Tuple[int, int, int]]], Any]
        ] = None,
        on_modifies: Optional[Callable[[Span, Span, Span], bool]] = None,
        allowed_types: Optional[Set[str]] = None,
        excluded_types: Optional[Set[str]] = None,
        max_scope: Optional[int] = None,
        max_targets: Optional[int] = None,
        terminated_by: Optional[Set[str]] = None,
        metadata: Optional[Dict[Any, Any]] = None,
    ):
        """
        Create an ConTextRule object.
        The primary arguments of `literal` `category`, and `direction` define the span of text to be matched, the
        semantic category, and the direction within the sentence in which the modifier operates.
        Other arguments specify additional custom logic such as:
            - Additional control over what text can be matched as a modifier (pattern and on_match)
            - Which types of targets can be modified (allowed_types, excluded_types)
            - The scope size and number of targets that a modifier can modify (max_targets, max_scope)
            - Other logic for terminating a span or for allowing a modifier to modify a target (on_modifies,
            terminated_by)

        Args:
            literal: The string representation of a concept. If `pattern` is None, this string will be lower-cased and
                matched to the lower-case string. If `pattern` is not None, this argument will not be used for matching
                but can be used as a reference as the rule name.
            category: The semantic class of the matched span. This corresponds to the `label_` attribute of an entity.
            pattern: A list or string to use as a spaCy pattern rather than `literal`. If a list, will use spaCy
                token-based pattern matching to match using token attributes. If a string, will use medspaCy's
                RegexMatcher. If None, will use `literal` as the pattern for phrase matching. For more information, see
                https://spacy.io/usage/rule-based-matching.
            direction: The directionality or action of a modifier. This defines which part of a sentence a modifier will
                include as its scope. Entities within the scope will be considered to be modified.
                Valid values are:
                - "FORWARD": Scope will begin after the end of a modifier and move to the right
                - "BACKWARD": Scope will begin before the beginning of a modifier and move to the left
                - "BIDIRECTIONAL": Scope will expand on either side of a modifier
                - "TERMINATE": A special direction to limit any other modifiers if this phrase is in its scope. Example:
                    "no evidence of chf but there is pneumonia": "but" will prevent "no evidence of" from modifying
                    "pneumonia"
                - "PSEUDO": A special direction which will not modify any targets. This can be used for differentiating
                    superstrings of modifiers. Example: A modifier with literal="negative attitude" will prevent the
                    phrase "negative" in "She has a negative attitude about her treatment" from being extracted as a
                    modifier.
            on_match: An optional callback function or other callable which takes 4 arguments: `(matcher, doc, i,
                matches)`. For more information, see https://spacy.io/usage/rule-based-matching#on_match
            on_modifies: Callback function to run when building an edge between a target and a modifier. This allows
                specifying custom logic for allowing or preventing certain modifiers from modifying certain targets. The
                callable should take 3 arguments:
                    target: The spaCy Span from doc.ents (ie., 'Evidence of pneumonia')
                    modifier: The spaCy Span covered in a resulting modifier (ie., 'no evidence of')
                    span_between: The Span between the target and modifier in question.
                Should return either True or False. If returns False, then the modifier will not modify the target.
            allowed_types: A collection of target labels to allow a modifier to modify. If None, will apply to any type
                not specifically excluded in excluded_types. Only one of allowed_types and excluded_types can be used.
                An error will be thrown if both are not None.
            excluded_types: A collection of target labels which this modifier cannot modify. If None, will apply to all
                target types unless allowed_types is not None.
            max_scope: A number of tokens to explicitly limit the size of the modifier's scope. If None, the scope will
                include the entire sentence in the direction of `direction` and the entire sentence for "BIDIRECTIONAL".
                This is useful for requiring modifiers be very close to a concept in the text or for preventing long
                modifier ranges caused by sentence splitting problems.
            max_targets: The maximum number of targets which a modifier can modify. If None, will modify all targets in
                its scope.
            terminated_by: An optional collection of other modifier categories which will terminate the scope of this
                modifier. If None, only "TERMINATE" will do this. Example: if a ConTextRule defining "positive for" has
                terminated_by={"NEGATED_EXISTENCE"}, then in the sentence "positive for flu, negative for RSV", the
                positive modifier will modify "flu" but will be terminated by "negative for" and will not modify "RSV".
                This helps prevent multiple conflicting modifiers from distributing too far across a sentence.
            metadata: Optional dictionary of any extra metadata.
        """
        super().__init__(literal, category.upper(), pattern, on_match, metadata)
        self.on_modifies = on_modifies

        if allowed_types is not None and excluded_types is not None:
            raise ValueError(
                "A ConTextRule was instantiated with non-null values for both allowed_types and excluded_types. "
                "Only one of these can be non-null."
            )
        if allowed_types is not None:
            self.allowed_types = {label.upper() for label in allowed_types}
        else:
            self.allowed_types = None
        if excluded_types is not None:
            self.excluded_types = {label.upper() for label in excluded_types}
        else:
            self.excluded_types = None

        if max_targets is not None and max_targets <= 0:
            raise ValueError("max_targets must be >= 0 or None.")
        self.max_targets = max_targets
        if max_scope is not None and max_scope <= 0:
            raise ValueError("max_scope must be >= 0 or None.")
        self.max_scope = max_scope
        if terminated_by is None:
            terminated_by = set()
        else:
            if isinstance(terminated_by, str):
                raise ValueError(
                    f"terminated_by must be an iterable, such as a list or set, not {terminated_by}."
                )
            terminated_by = {string.upper() for string in terminated_by}

        self.terminated_by = terminated_by

        self.metadata = metadata

        if direction.upper() not in self._ALLOWED_DIRECTIONS:
            raise ValueError(
                "Direction {0} not recognized. Must be one of: {1}".format(
                    direction, self._ALLOWED_DIRECTIONS
                )
            )
        self.direction = direction.upper()

    @classmethod
    def from_json(cls, filepath) -> List[ConTextRule]:
        """Read in a lexicon of modifiers from a JSON file under the key `context_rules`.

        Args:
            filepath: The .json file containing modifier rules. Must contain `context_rules` key containing the rule
                JSONs.

        Returns:
            A list of ConTextRules objects read from the JSON.
        """

        with open(filepath) as file:
            modifier_data = json.load(file)
        context_rules = []
        for data in modifier_data["context_rules"]:
            context_rules.append(ConTextRule.from_dict(data))
        return context_rules

    @classmethod
    def from_dict(cls, rule_dict) -> ConTextRule:
        """Reads a dictionary into a ConTextRule.

        Args:
            rule_dict: The dictionary to convert.

        Returns:
            The ConTextRule created from the dictionary.
        """
        keys = set(rule_dict.keys())
        invalid_keys = keys.difference(cls._ALLOWED_KEYS)
        if invalid_keys:
            msg = (
                "JSON object contains invalid keys: {0}.\n"
                "Must be one of: {1}".format(invalid_keys, cls._ALLOWED_KEYS)
            )
            raise ValueError(msg)
        rule = ConTextRule(**rule_dict)
        return rule

    def to_dict(self) -> Dict[str, str]:
        """Converts ConTextItems to a python dictionary. Used when writing context rules to a json file.

        Returns:
            The dictionary containing the ConTextRule info.
        """
        rule_dict = {}
        for key in self._ALLOWED_KEYS:
            value = self.__dict__.get(key)
            if value is not None:
                rule_dict[key] = value
        return rule_dict

    def __repr__(self):
        return (
            f"ConTextRule(literal='{self.literal}', category='{self.category}', pattern={self.pattern}, "
            f"direction='{self.direction}')"
        )
