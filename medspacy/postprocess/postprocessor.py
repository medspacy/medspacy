from collections import namedtuple
from typing import Iterable, Union, List, Literal

from spacy.language import Language
from spacy.tokens import Doc

from medspacy.postprocess import PostprocessingRule

postprocess_pattern = namedtuple(
    "PostProcessPattern", ["func", "attr", "check_value", "success_value"]
)


@Language.factory("medspacy_postprocessor")
class Postprocessor:
    def __init__(
        self,
        nlp: Language,
        name: str = "medspacy_postprocessor",
        rules: Iterable[PostprocessingRule] = None,
        debug: bool = False,
        input_type: Literal["ents", "group"] = "ents",
        span_group_name: str = "medspacy_spans",
    ):
        self.nlp = nlp
        self.name = name
        self._rules = []
        self.debug = debug
        self._input_type = input_type
        self._span_group_name = span_group_name

        self.add(rules)

    @property
    def rules(self) -> List[PostprocessingRule]:
        """
        Gets the rules.

        Returns:
            The list of PostprocessingRules available to the Postprocessor.
        """
        return self._rules

    @property
    def input_type(self):
        """
        The input source of entities for the component. Must be either "ents" corresponding to doc.ents or "group" for
        a spaCy span group.

        Returns:
            The input type, "ents" or "group".
        """
        return self._input_type

    @input_type.setter
    def input_type(self, val):
        if not (val == "ents" or val == "group"):
            raise ValueError('input_type must be "ents" or "group".')
        self._input_type = val

    @property
    def span_group_name(self) -> str:
        """
        The name of the span group used by this component. If `input_type` is "group", calling this component will
        use spans in the span group with this name.

        Returns:
            The span group name.
        """
        return self._span_group_name

    @span_group_name.setter
    def span_group_name(self, name: str):
        if not name or not isinstance(name, str):
            raise ValueError("Span group name must be a string.")
        self._span_group_name = name

    def add(self, rules: Union[PostprocessingRule, Iterable[PostprocessingRule]]):
        """
        Adds PostprocessingRules to the Postprocessor.

        Args:
            rules: A single PostprocessingRule or a collection of PostprocessingRules to add to the Postprocessor.
        """
        if isinstance(rules, PostprocessingRule):
            rules = [rules]
        for rule in rules:
            if not isinstance(rule, PostprocessingRule):
                raise TypeError(
                    f"Rules must be type PostprocessingRule, not {type(rule)}."
                )
        self._rules += rules

    def __call__(self, doc: Doc):
        """
        Calls the Postprocessor on a spaCy doc. This will call each PostprocessingRule on the doc

        Args:
            doc: The Doc to process.

        Returns:
            The processed Doc.
        """
        # Iterate through the entities in reversed order
        if self._input_type == "ents":
            spans = doc.ents
        else:
            spans = doc.spans[self._span_group_name]

        for i in range(len(spans) - 1, -1, -1):
            ent = spans[i]
            if self.debug:
                print(ent)
            for rule in self.rules:
                rule(ent, i, self.debug)
                # Check if the entity was removed -if it was, skip to the next entity
                try:
                    if spans[i] != ent:
                        break
                except IndexError:
                    break
            # if self.debug:
            #     print()
        return doc
