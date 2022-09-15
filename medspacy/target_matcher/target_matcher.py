from typing import List, Union

from spacy.tokens import Doc, Span
from spacy.language import Language
from .target_rule import TargetRule
from ..common.medspacy_matcher import MedspacyMatcher


@Language.factory("medspacy_target_matcher")
class TargetMatcher:
    """
    TargetMatcher is a component for advanced direction-based text extraction. Rules are defined using
    `medspacy.target_matcher.TargetRule`.

    A `TargetMatcher` will use the added `TargetRule` objects to identify matches in the text and apply labels or modify
    attributes. It will either modify the input spaCy `Doc` with the result or return the spans as a list.

    In addition to extracting spans of text and setting labels, TargetRules can also define setting custom attributes
    and metadata. Additionally, each resulting span has an attribute span._.target_rule which maps a span to the
    TargetRule which set it.
    """

    def __init__(
        self,
        nlp: Language,
        name: str = "medspacy_target_matcher",
        phrase_matcher_attr: str = "LOWER",
        result_type: Union[str, None] = "ents",
        span_group_name: str = "medspacy_spans",
    ):
        """
        Creates a new TargetMatcher.

        Args:
            nlp: A spaCy Language model.
            name: The name of the TargetMatcher component
            phrase_matcher_attr: The token attribute to use for PhraseMatcher for rules where `pattern` is None. Default
                is 'LOWER'.
            result_type: "ents" (default), "group", or None. Determines where TargetMatcher will put the matched spans.
                "ents" will add spans to doc.ents and add to any existing entities. If conflicts appear, existing
                entities will take precedence. "group" will add spans to doc.spans under the specified group name. None
                will return the list of spans rather than saving to the Doc.
            span_group_name: The name of the span group used to store results when result_type is "group". Default is
                "medspacy_spans".
        """
        self.nlp = nlp
        self.name = name
        self.result_type = result_type
        self.span_group_name = span_group_name
        self._rules = list()

        self.labels = set()

        self.matcher = MedspacyMatcher(nlp, phrase_matcher_attr=phrase_matcher_attr)
        self._rule_item_mapping = self.matcher._rule_item_mapping

    def add(self, rules: list):
        """
        Adds a list of TargetRules to the TargetMatcher.

        Args:
            rules: A collection of TargetRules.

        Raises:
            ValueError: All elements in rules must be TargetRules.
        """
        for rule in rules:
            if not isinstance(rule, TargetRule):
                raise ValueError("Rules must be TargetRule, not", type(rule))
        self._rules += rules
        self.matcher.add(rules)

    @property
    def rules(self) -> List[TargetRule]:
        """
        Gets the list of TargetRules for the TargetMatcher.

        Returns:
            A list of TargetRules.
        """
        return self._rules

    def __call__(self, doc: Doc) -> Union[Doc, List[Span]]:
        """
        Calls TargetMatcher on a Doc. By default and when `result_type` is "ents", adds results to doc.ents. If
        `result_type` is "group", adds results to the span group specified by `span_group_name`. If `result_type` is
        None, then returns a list of the matched Spans.

        Args:
            doc: The spaCy Doc to process.

        Returns:
            Returns a modified `doc` when `TargetMatcher.result_type` is "ents" or "group". Returns a list of
            `Span` objects if `TargetMatcher.result_type` is None.
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
        if self.result_type.lower() is "ents":
            for span in spans:
                try:
                    doc.ents += (span,)
                # spaCy will raise a value error if the token in span are already part of an entity (i.e., as part of an
                # upstream component). In that case, let the existing span supersede this one.
                except ValueError as e:
                    # raise e
                    pass
            return doc
        elif self.result_type.lower() is "group":
            doc.spans[self.span_group_name] = spans
        else:
            return spans
