from typing import List, Union

from . import TargetRule
from ..common.medspacy_matcher import MedspacyMatcher
from spacy.tokens import Token, Doc
from spacy.language import Language


@Language.factory("medspacy_concept_tagger")
class ConceptTagger:
    """ConceptTagger is a component for setting an attribute on tokens contained in spans extracted by TargetRules. This
    can be used for tasks such as semantic labeling or for normalizing tokens, making downstream extraction simpler.

    A common use case is when a single concept can have many synonyms or variants and downstream rules would be
    simplified by matching on a unified token tag for those synonyms rather than including the entire synonym list in
    each downstream rule.
    """

    def __init__(
        self,
        nlp: Language,
        name: str = "medspacy_concept_tagger",
        attr_name: str = "concept_tag",
    ):
        """
        Creates a new ConceptTagger.

        Args:
            nlp: A spaCy Language model.
            name: The name of the ConceptTagger component. Must be a valid python variable name.
            attr_name: The name of the attribute to set to tokens.
        """
        self.nlp = nlp
        self.name = name
        self._attr_name = attr_name
        self.__matcher = MedspacyMatcher(nlp)

        # If the token attribute hasn't been set, add it now
        # try:
        #     Token.set_extension(attr_name, default="")
        # except:
        #     pass

        # not sure if silent errors here are beneficial, removing try statement for now.
        Token.set_extension(self._attr_name, default="")

    @property
    def attr_name(self) -> str:
        """
        The name of the attribute that will be set on each matched token.

        Returns:
            The attribute name.
        """
        return self._attr_name

    def add(self, rules: Union[TargetRule, List[TargetRule]]):
        """
        Adds a single TargetRule or a list of TargetRules to the ConceptTagger.

        Args:
            rules: A single TargetRule or a collection of TargetRules.
        """
        self.__matcher.add(rules)

    def __call__(self, doc: Doc) -> Doc:
        """
        Call ConceptTagger on a doc. Matches spans and assigns attributes to all tokens contained in those spans, but
        does not preserve the spans themselves.

        Args:
            doc: The spaCy Doc to process.

        Returns:
            The spaCy Doc processed.
        """
        matches = self.__matcher(doc)
        for (rule_id, start, end) in matches:
            rule = self.__matcher.rule_map[self.nlp.vocab.strings[rule_id]]
            for i in range(start, end):
                setattr(doc[i]._, self.attr_name, rule.category)

        return doc
