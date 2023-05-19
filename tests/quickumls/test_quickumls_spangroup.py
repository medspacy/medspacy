import spacy
import warnings
from sys import platform
import pytest
from os import path
from pathlib import Path

import medspacy

from quickumls import spacy_component

from medspacy.util import get_quickumls_demo_dir

MEDSPACY_DEFAULT_SPAN_GROUP_NAME = "medspacy_spans"

# allow default QuickUMLS (very small sample data) to be loaded
nlp = spacy.blank("en")

# Configure the QuickUMLS component for these tests on SpanGroups
# Some allow overlaps, but this config will currently work for all of the tests below
nlp.add_pipe(
    "medspacy_quickumls",
    config={
        "threshold": 0.7,
        "result_type": "group",
        # do not constrain to the best match for overlapping
        "best_match": False,
        "quickumls_fp": get_quickumls_demo_dir(),
    },
)


class TestQuickUMLSSpanGroup:
    def test_span_groups(self):
        """
        Test that span groups can bs used as a result type (as opposed to entities)
        """

        concept_term = "dipalmitoyllecithin"

        text = "Decreased {} content found in lung specimens".format(concept_term)

        doc = nlp(text)

        assert len(doc.ents) == 0

        assert len(doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME]) == 1

        span = doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME][0]

        assert len(span._.umls_matches) > 0

    def test_overlapping_spans(self):
        """
        Test that overlapping terms can be extracted
        """

        # the demo data contains both of these concepts, so let's put them together
        # and allow overlap on one of the tokens
        # dipalmitoyl phosphatidylcholine
        # phosphatidylcholine, dipalmitoyl
        text = """dipalmitoyl phosphatidylcholine dipalmitoyl"""

        doc = nlp(text)

        assert len(doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME]) >= 2

    def test_multiword_span(self):
        """
        Test that an extraction can be made on a concept with multiple words
        """

        # the demo data contains this concept:
        # dipalmitoyl phosphatidylcholine
        text = """dipalmitoyl phosphatidylcholine"""

        doc = nlp(text)

        assert len(doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME]) == 1
