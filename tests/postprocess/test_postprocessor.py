import spacy
from spacy.language import Language
from spacy.tokens import Span, Doc

from medspacy.postprocess import Postprocessor
from medspacy.postprocess import PostprocessingRule
from medspacy.postprocess import PostprocessingPattern
from medspacy.postprocess import postprocessing_functions

import pytest

import re

import tempfile

nlp = spacy.load("en_core_web_sm")

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

        """Test that the post processor executes a rule."""
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

