import os, sys
sys.path.append(os.getcwd())
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


class TestQuickUMLSSpanGroup:
    def test_span_groups(self, quickumls_nlp):
        """
        Test that span groups can bs used as a result type (as opposed to entities)
        """

        quickumls = quickumls_nlp.get_pipe("medspacy_quickumls")
        quickumls.result_type = "group"

        concept_term = "dipalmitoyllecithin"

        text = "Decreased {} content found in lung specimens".format(concept_term)

        doc = quickumls_nlp(text)

        assert len(doc.ents) == 0

        assert len(doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME]) == 1

        span = doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME][0]

        assert len(span._.umls_matches) > 0

    def test_overlapping_spans(self, quickumls_nlp):
        """
        Test that overlapping terms can be extracted
        """

        quickumls = quickumls_nlp.get_pipe("medspacy_quickumls")
        quickumls.result_type = "group"

        # the demo data contains both of these concepts, so let's put them together
        # and allow overlap on one of the tokens
        # dipalmitoyl phosphatidylcholine
        # phosphatidylcholine, dipalmitoyl
        text = """dipalmitoyl phosphatidylcholine dipalmitoyl"""

        doc = quickumls_nlp(text)

        assert len(doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME]) >= 2

    def test_multiword_span(self, quickumls_nlp):
        """
        Test that an extraction can be made on a concept with multiple words
        """

        quickumls = quickumls_nlp.get_pipe("medspacy_quickumls")
        quickumls.result_type = "group"

        # the demo data contains this concept:
        # dipalmitoyl phosphatidylcholine
        text = """dipalmitoyl phosphatidylcholine"""

        doc = quickumls_nlp(text)

        assert len(doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME]) == 1
