# from nlp_tools.utils import prune_overlapping_matches

from spacy.tokens import Token
from spacy.tokens import Span
from spacy.language import Language
from .target_rule import TargetRule
from ..common.medspacy_matcher import MedspacyMatcher


@Language.factory("medspacy_target_matcher")
class TargetMatcher:
    """TargetMatcher is a component for advanced direction-based text extraction.
    Rules are defined using medspacy.target_matcher.TargetRule.
    """

    def __init__(
        self, nlp, name="medspacy_target_matcher", add_ents=True, phrase_matcher_attr="LOWER"
    ):
        """Create a new TargetMatcher.
        Params:
            nlp: A spaCy Language model.
            add_ents: Whether to add extracted spans to doc.ents. If True, will attempt to add
                resulting entities to existing ents. If resulting spans conflict with existing ents,
                the existing entities will take precedence.
                If False, will return a list of spans.
            phrase_matcher_attr: The token attribute to use for PhraseMatcher for rules where `pattern` is None.
                Default is "LOWER".
        """
        self.nlp = nlp
        self.name = name
        self.add_ents = add_ents
        self._rules = list()

        self.labels = set()

        self.matcher = MedspacyMatcher(nlp, phrase_matcher_attr=phrase_matcher_attr)
        self._rule_item_mapping = self.matcher._rule_item_mapping

    def add(self, rules):
        """Add a list of targetRules to the matcher."""
        if not isinstance(rules, list):
            rules = [rules]
        self._rules += rules
        self.matcher.add(rules)
        for rule in rules:
            if not isinstance(rule, TargetRule):
                raise ValueError("Rules must be TargetRule, not", type(rule))

    @property
    def rules(self):
        return self._rules

    def __call__(self, doc):
        """Call TargetMatcher on a doc. If `add_ents=True`, then matched
        spans will be merged in to doc.ents and `doc` will be returned.
        If `add_ents=False`, then matched spans will be returned as a list,
        in which case this cannot be used as part of a spaCy pipeline, which
        requires each component to return the doc, but can be used as a standalone matcher.

        In addition to extracting spans of text and setting labels, TargetRules
        can also define setting custom attributes and metadata. Additionally,
        each resulting span has an attribute span._.target_rule which maps
        a span to the TargetRule which set it.
        """
        matches = self.matcher(doc)
        spans = []
        for (rule_id, start, end) in matches:
            rule = self._rule_item_mapping[self.nlp.vocab.strings[rule_id]]
            span = Span(doc, start=start, end=end, label=rule.category)
            span._.target_rule = rule
            if rule.attributes is not None:
                for (attribute, value) in rule.attributes.items():
                    try:
                        setattr(span._, attribute, value)
                    except AttributeError as e:
                        raise e
            spans.append(span)
        if self.add_ents is True:
            for span in spans:
                try:
                    doc.ents += (span,)
                # spaCy will raise a value error if the token in span are already
                # part of an entity (ie., as part of an upstream component)
                # In that case, let the existing span supersede this one
                except ValueError as e:
                    # raise e
                    pass
            return doc
        else:
            return spans
