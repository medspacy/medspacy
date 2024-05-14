import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
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

LANGUAGE = 'es'

class TestQuickUMLSSpanGroupES:
    def test_span_groups_es(self):
        """
        Test that span groups can bs used as a result type (as opposed to entities)
        """

        # allow default QuickUMLS (very small sample data) to be loaded

        nlp = spacy.blank(LANGUAGE)

        # Configure the QuickUMLS component for these tests on SpanGroups
        # Some allow overlaps, but this config will currently work for all of the tests below
        nlp.add_pipe(
            "medspacy_quickumls",
            config={
                "threshold": 0.7,
                "result_type": "group",
                # do not constrain to the best match for overlapping
                "best_match": False,
                "quickumls_fp": get_quickumls_demo_dir(LANGUAGE),
            },
        )

        concept_term = "dipalmitoilfosfatidilcolina"

        text = "{} en los pulmones".format(concept_term)

        doc = nlp(text)

        assert len(doc.ents) == 0

        assert len(doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME]) == 1

        span = doc.spans[MEDSPACY_DEFAULT_SPAN_GROUP_NAME][0]

        assert len(span._.umls_matches) > 0


