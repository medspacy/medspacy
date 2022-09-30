from typing import Iterable, List, Dict, Tuple, Set

import spacy
from spacy import Language
from spacy.matcher import Matcher, PhraseMatcher
from .regex_matcher import RegexMatcher
from .base_rule import BaseRule
from .util import prune_overlapping_matches

from spacy.tokens import Doc


class MedspacyMatcher:
    """
    MedspacyMatcher is a class which combines spaCy's Matcher and PhraseMatcher classes along with medspaCy's
    RegexMatcher and acts as one single matcher using 3 different types of rules:
        - Exact phrases
        - List of dictionaries for matching on token attributes (see https://spacy.io/usage/rule-based-matching#matcher)
        - Regular expression matches. Note that regular-expression matching is not natively supported by spaCy and could
                result in unexpected matched spans if match boundaries do not align with token boundaries.
    Rules can be defined by any class which inherits from medspacy.common.BaseRule, such as:
        medspacy.target_matcher.TargetRule
        medspacy.context.ConTextRule
    """

    name = "medspacy_matcher"

    def __init__(
        self, nlp: Language, phrase_matcher_attr: str = "LOWER", prune: bool = True
    ):
        """
        Creates a MedspacyMatcher.

        Args:
            nlp: A spaCy Language model.
            phrase_matcher_attr: The attribute to use for spaCy's PhraseMatcher. Default is 'LOWER'.
            prune: Whether to prune matches that overlap or are substrings of another match. For example, if "no history
                of" and "history of" are both matches, setting prune to True would drop "history of". Default is True.
        """
        self.nlp = nlp.tokenizer # preserve only the tokenizer for creating phrasematcher rules
        self._rule_ids = set()
        self._labels = set()
        self._rule_map = dict()
        self._prune = prune
        self.__matcher = Matcher(nlp.vocab)
        self.__phrase_matcher = PhraseMatcher(nlp.vocab, attr=phrase_matcher_attr)
        self.__regex_matcher = RegexMatcher(nlp.vocab)

        self.__rule_count = 0
        self.__phrase_matcher_attr = phrase_matcher_attr

    @property
    def rules(self) -> List[BaseRule]:
        """
        The list of rules used by the MedspacyMatcher.

        Returns:
            A list of rules, all of which inherit from BaseRule.
        """
        return list(self._rule_map.values())

    @property
    def rule_map(self) -> Dict[str, BaseRule]:
        """
        The dictionary mapping a rule's id to the rule object.

        Returns:
            A dictionary mapping the rule's id to the rule.
        """
        return self._rule_map

    @property
    def labels(self) -> Set[str]:
        """
        The set of labels available to the matcher.

        Returns:
            A set of labels containing the labels for all the rules added to the matcher.
        """
        return self._labels

    def add(self, rules: Iterable[BaseRule]):
        """
        Adds a collection of rules to the matcher. Rules must inherit from `medspacy.common.BaseRule`.

        Args:
            rules: A collection of rules. Each rule must inherit from `medspacy.common.BaseRule`.
        """
        for rule in rules:
            if not isinstance(rule, BaseRule):
                raise TypeError("Rules must inherit from medspacy.common.BaseRule.")
            self._labels.add(rule.category)
            rule_id = f"{rule.category}_{self.__rule_count}"
            rule._rule_id = rule_id
            self._rule_map[rule_id] = rule
            if rule.pattern is not None:
                # If it's a string, add a RegEx
                if isinstance(rule.pattern, str):
                    self.__regex_matcher.add(rule_id, [rule.pattern], rule.on_match)
                # If it's a list, add a pattern dictionary
                elif isinstance(rule.pattern, list):
                    self.__matcher.add(rule_id, [rule.pattern], on_match=rule.on_match)
                else:
                    raise ValueError(
                        f"The pattern argument must be either a string or a list, not {type(rule.pattern)}"
                    )
            else:
                if self.__phrase_matcher_attr.lower() == "lower":
                    # only lowercase when the phrase matcher is looking for lowercase matches.
                    text = rule.literal.lower()
                else:
                    # otherwise, expect users to handle phrases as aligned with their non-default phrase matching scheme
                    # this prevents .lower() from blocking matches on attrs like ORTH or UPPER
                    text = rule.literal
                doc = self.nlp(text)
                self.__phrase_matcher.add(
                    rule_id,
                    [doc],
                    on_match=rule.on_match,
                )
            self.__rule_count += 1

    def __call__(self, doc: Doc) -> List[Tuple[int, int, int]]:
        """
        Call MedspacyMatcher on a doc and return a single list of matches. If self.prune is True,
        in the case of overlapping matches the longest will be returned.

        Args:
            doc: The spaCy Doc to process.

        Returns:
            A list of tuples, each containing 3 ints representing the individual match (match_id, start, end).
        """
        matches = self.__matcher(doc)
        matches += self.__phrase_matcher(doc)
        matches += self.__regex_matcher(doc)
        if self._prune:
            matches = prune_overlapping_matches(matches)
        return matches
