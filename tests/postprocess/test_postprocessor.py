import spacy
from spacy.language import Language
from spacy.tokens import Span, Doc

from medspacy.target_matcher import TargetMatcher, TargetRule
from medspacy.postprocess import Postprocessor
from medspacy.postprocess import PostprocessingRule
from medspacy.postprocess import PostprocessingPattern
from medspacy.postprocess import postprocessing_functions

from typing import Iterable, Union, Literal

import pytest

import re

import tempfile

nlp = spacy.load("en_core_web_sm")

# Simple helper function to remove span groups
def remove_span_group(ent: Span,
    i: int,
    input_type: Literal["ents", "group"] = "ents",
    span_group_name: str = "medspacy_spans"):
    return postprocessing_functions.remove_ent(ent, i, "group", span_group_name)

class TestPostprocessor:
    def test_post_processor(self):
        """Test that the post processor executes a rule."""
        doc = nlp("There is shortness of breath.")
        doc.ents = (Span(doc, 2, 5, "CONDITION"),)

        postprocessor = Postprocessor(nlp)

        # let's add just one single rule with a very simple and naive pattern
        postprocessing_rules = [
            PostprocessingRule(
                patterns=[
                    PostprocessingPattern(lambda ent: ent is not None, True),
                ],
                action=postprocessing_functions.remove_ent,
                description="Remove any entity found."
            ),
        ]

        postprocessor.add(postprocessing_rules)

        doc = postprocessor(doc)

        # make sure we have no entities now (the rules actually ran)

        assert len(doc.ents) == 0

    def test_post_processor_execute_all_rules(self):
        """Test that the post processor executes all configured rules.
            See more here: https://github.com/medspacy/medspacy/issues/213"""
        doc = nlp("There is shortness of breath.")

        # NOTE: Since the issue this reproduces will check for two things which should not be
        # compared, the easiest way to show this is with a multi-word entity
        doc.ents = (Span(doc, 2, 5, "CONDITION"),)

        postprocessor = Postprocessor(nlp)

        # let's add just two rules
        # The first one should not actually perform an action, but is here for the example
        # The second one should actually perform an action, but this tests the expectation issue
        postprocessing_rules = [
            PostprocessingRule(
                patterns=[
                    PostprocessingPattern(lambda ent: ent.text == "SomeOtherEntity", True),
                ],
                action=postprocessing_functions.remove_ent,
                description="Remove an entity with a specific name which will not be in this tests"
            ),
            PostprocessingRule(
                patterns=[
                    PostprocessingPattern(lambda ent: ent is not None, True),
                ],
                action=postprocessing_functions.remove_ent,
                description="Remove any entity found."
            )
        ]

        postprocessor.add(postprocessing_rules)

        doc = postprocessor(doc)

        # make sure we have no entities now (all of the rules actually ran)

        assert len(doc.ents) == 0

    def test_post_processor_execute_all_rules_span_groups(self):
        """Test that the post processor executes all configured rules, but this time with Span Groups
            See more here: https://github.com/medspacy/medspacy/issues/213"""

        matcher = TargetMatcher(nlp, result_type="group")
        matcher.add([TargetRule("shortness of breath", "CONDITION", pattern=[{"LOWER": "shortness"},
                                                                             {"LOWER": "of"},
                                                                             {"LOWER": "breath"}])])
        doc = nlp("There is shortness of breath")
        matcher(doc)
        assert len(doc.spans["medspacy_spans"]) == 1

        # this time it works on group
        postprocessor = Postprocessor(nlp, input_span_type = "group")

        # let's add just two rules
        # The first one should not actually perform an action, but is here for the example
        # The second one should actually perform an action, but this tests the expectation issue
        postprocessing_rules = [
            PostprocessingRule(
                patterns=[
                    PostprocessingPattern(lambda span: span.text == "SomeOtherEntity", True),
                ],
                action=remove_span_group,
                description="Remove an entity with a specific name which will not be in this tests"
            ),
            PostprocessingRule(
                patterns=[
                    PostprocessingPattern(lambda span: span is not None, True),
                ],
                action=remove_span_group,
                description="Remove any entity found."
            )
        ]

        postprocessor.add(postprocessing_rules)

        doc = postprocessor(doc)

        # make sure we have no spans now (all of the rules actually ran)

        assert len(doc.spans["medspacy_spans"]) == 0

