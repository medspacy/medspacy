from __future__ import annotations
from typing import Dict, Callable, Any, List, Tuple

from spacy.matcher import Matcher
from spacy.tokens import Doc

from ..common.base_rule import BaseRule


class TargetRule(BaseRule):
    """
    TargetRule defines rules for extracting entities from text using TargetMatcher.
    """

    _ALLOWED_KEYS = {
        "literal",
        "pattern",
        "category",
        "metadata",
        "attributes",
    }

    def __init__(
        self,
        literal: str,
        category: str,
        pattern: Dict = None,
        on_match: Callable[[Matcher, Doc, int, List[Tuple[int, int, int]]], Any] = None,
        metadata: Dict = None,
        attributes: Dict = None,
    ):
        """
        Creates a new TargetRule.

        Args:
            literal: The actual string of a concept. If pattern is None, this string will be lower-cased and matched to
                the lower-case string. If `pattern` is not None, this argument will not be used for actual matching but
                can be used as a reference as the direction name.
            category: The semantic class of the matched span. This corresponds to the `label_` attribute of an entity.
            pattern: A pattern to use for matching rather than `literal`. If a list, will use spaCy dictionary pattern
                matching to match using token attributes. See https://spacy.io/usage/rule-based-matching.
            on_match: An optional callback function or other callable which takes 4 arguments: `(matcher, doc, i,
                matches)`. For more information, see https://spacy.io/usage/rule-based-matching#on_match
            metadata: Optional dictionary of metadata.
            attributes: Optional custom attribute names to set for a Span matched by the direction. These attribute
                names are stored under Span._.[attribute_name]. For example, if `attributes={'is_historical':True}`,
                then any spans matched by this direction will have span._.is_historical = True
        """
        super().__init__(literal, category, pattern, on_match, metadata)
        self.attributes = attributes
        self._rule_id = None

    @classmethod
    def from_json(cls, filepath: str) -> List[TargetRule]:
        """Read in a lexicon of modifiers from a JSON file.

        Args:
            filepath: the .json file containing modifier rules

        Returns:
            context_item: A list of ConTextRule objects.

        Raises:
            KeyError: If the dictionary contains any keys other than
                those accepted by ConTextRule.__init__
        """
        import json

        with open(filepath) as file:
            target_data = json.load(file)
        target_rules = []
        for data in target_data["target_rules"]:
            target_rules.append(TargetRule.from_dict(data))
        return target_rules

    @classmethod
    def from_dict(cls, rule_dict: Dict) -> TargetRule:
        """Reads a dictionary into a ConTextRule. Used when reading from a json file.

        Args:
            rule_dict: the dictionary to convert

        Returns:
            The ConTextRule created from the dictionary

        Raises:
            ValueError: if the json is invalid
        """
        keys = set(rule_dict.keys())
        invalid_keys = keys.difference(cls._ALLOWED_KEYS)
        if invalid_keys:
            msg = (
                "JSON object contains invalid keys: {0}.\n"
                "Must be one of: {1}".format(invalid_keys, cls._ALLOWED_KEYS)
            )
            raise ValueError(msg)
        rule = TargetRule(**rule_dict)
        return rule

    @classmethod
    def to_json(cls, target_rules: List[TargetRule], filepath: str):
        """Writes ConTextItems to a json file.

        Args:
            target_rules: a list of TargetRules that will be written to a file.
            filepath: the .json file to contain modifier rules
        """
        import json

        data = {"target_rules": [rule.to_dict() for rule in target_rules]}
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)

    def to_dict(self):
        """Converts TargetRules to a python dictionary. Used when writing target rules to a json file.

        Returns:
            The dictionary containing the TargetRule info.
        """
        rule_dict = {}
        for key in self._ALLOWED_KEYS:
            value = self.__dict__.get(key)
            if value is not None:
                rule_dict[key] = value
        return rule_dict

    def __repr__(self):
        return f"""TargetRule(literal="{self.literal}", category="{self.category}", pattern={self.pattern}, attributes={self.attributes}, on_match={self.on_match})"""
