from typing import List

from . import TargetMatcher
from spacy.tokens import Token, Doc
from spacy.language import Language


@Language.factory("medspacy_concept_tagger")
class ConceptTagger:
    """ConceptTagger is a component for setting an attribute on tokens contained in spans extracted by TargetRules. This
    can be used for tasks such as semantic labeling or for normalizing tokens, making downstream extraction simpler.
    """

    def __init__(
        self,
        nlp: Language,
        name: str = "medspacy_concept_tagger",
        attr_name: str = "concept_tag",
        span_group_name: str = "medspacy_spans",
    ):
        """
        Creates a new ConceptTagger.

        Args:
            nlp: A spaCy Language model.
            name: The name of the ConceptTagger component
            attr_name: The name of the attribute to set to tokens.
            span_group_name: The name of the span group used to store results. Default is "medspacy_spans".
        """
        self.nlp = nlp
        self.name = name
        self.attr_name = attr_name
        self.target_matcher = TargetMatcher(nlp, result_type=None)
        self.rules = []
        self.span_group_name = span_group_name

        # If the token attribute hasn't been set, add it now
        try:
            Token.set_extension(attr_name, default="")
        except:
            pass

    def add(self, rules: List):
        """

        Args:
            rules:
        """
        self.target_matcher.add(rules)
        for rule in rules:
            self.rules.append(rule)

    def __call__(self, doc: Doc) -> Doc:
        """

        Args:
            doc:

        Returns:

        """
        spans = self.target_matcher(doc)
        for span in spans:
            for token in span:
                setattr(token._, self.attr_name, span.label_)

        return doc
