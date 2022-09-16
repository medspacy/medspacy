from typing import List, Union, Iterable

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
        self._result_type = result_type
        self._span_group_name = span_group_name

        self.__matcher = MedspacyMatcher(nlp, phrase_matcher_attr=phrase_matcher_attr)

    @property
    def rules(self) -> List[TargetRule]:
        """
        Gets the list of TargetRules for the TargetMatcher.

        Returns:
            A list of TargetRules.
        """
        return self.__matcher.rules

    @property
    def result_type(self) -> Union[str, None]:
        """
        The result type of the TargetMatcher. "ents" indicates that calling TargetMatcher will store the results in
        doc.ents, "group" indicates that the results will be stored in the span group indicated by `span_group_name`,
        and None indicates that spans will be returned in a list.

        Returns:
            The result type string.
        """
        return self._result_type

    @result_type.setter
    def result_type(self, result_type: Union[str, None]):
        if not (
            not result_type or result_type.lower() == "group" or result_type != "ents"
        ):
            raise ValueError('result_type must be "ent". "group" or None.')
        self._result_type = result_type

    @property
    def span_group_name(self) -> str:
        """
        The name of the span group used by this component. If `result_type` is "group", calling this component will
        place results in the span group with this name.

        Returns:
            The span group name.
        """
        return self._span_group_name

    @span_group_name.setter
    def span_group_name(self, name: str):
        if not name or not isinstance(name, str):
            raise ValueError("Span group name must be a string.")
        self._span_group_name = name

    def add(self, rules: Union[TargetRule, Iterable[TargetRule]]):
        """
        Adds a single TargetRule or a list of TargetRules to the TargetMatcher.

        Args:
            rules: A single TargetRule or a collection of TargetRules.
        """
        if isinstance(rules, TargetRule):
            rules = [rules]
        for rule in rules:
            if not isinstance(rule, TargetRule):
                raise TypeError("Rules must be TargetRule, not", type(rule))
        self.__matcher.add(rules)

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
        matches = self.__matcher(doc)
        spans = []
        for (rule_id, start, end) in matches:
            rule = self.__matcher.rule_map[self.nlp.vocab.strings[rule_id]]
            span = Span(doc, start=start, end=end, label=rule.category)
            span._.target_rule = rule
            if rule.attributes is not None:
                for (attribute, value) in rule.attributes.items():
                    try:
                        setattr(span._, attribute, value)
                    except AttributeError as e:
                        raise e
            spans.append(span)

        if not self.result_type:
            return spans
        elif self.result_type.lower() == "ents":
            for span in spans:
                try:
                    doc.ents += (span,)
                except ValueError:
                    # spaCy will raise a value error if the token in span are already part of an entity (i.e., as part
                    # of an upstream component). In that case, let the existing span supersede this one.
                    raise RuntimeWarning(
                        f'The result ""{span}"" conflicts with a pre-existing entity in doc.ents. This result has been '
                        f"skipped."
                    )
            return doc
        elif self.result_type.lower() == "group":
            doc.spans[self.span_group_name] = spans
            return doc
