import os, sys
sys.path.append(os.getcwd())
import spacy
import warnings
from sys import platform
import pytest
from os import path
from pathlib import Path

import medspacy

from medspacy.util import get_quickumls_demo_dir

MEDSPACY_DEFAULT_SPAN_GROUP_NAME = "medspacy_spans"


class TestQuickUMLSEntity:
    def test_initialize_pipeline(self, quickumls_nlp):
        """
        Test that a pipeline with a QuickUMLS component can be loaded in medpacy
        """

        assert quickumls_nlp

        quickumls = quickumls_nlp.get_pipe("medspacy_quickumls")
        assert quickumls
        assert quickumls.quickumls
        assert quickumls.quickumls.ss_db

    def test_quickumls_extractions(self, quickumls_nlp):
        """
        Test that extractions can be performed using the very small (<100 concept) UMLS sample resources
        """

        quickumls = quickumls_nlp.get_pipe("medspacy_quickumls")
        quickumls.result_type = "ents"

        doc = quickumls_nlp("Decreased dipalmitoyllecithin content found in lung specimens")

        assert len(doc.ents) == 1

        entity_spans = [ent.text for ent in doc.ents]

        assert "dipalmitoyllecithin" in entity_spans

    def test_min_similarity_threshold(self, quickumls_nlp):
        """
        Test that an extraction is NOT made if we set our matching to be perfect matching (100% similarity)
        and we have a typo
        """

        quickumls = quickumls_nlp.get_pipe("medspacy_quickumls")
        original_threshold = quickumls.quickumls.threshold
        quickumls.quickumls.threshold = 1.0
        quickumls.quickumls.ss_db.db.threshold = 1.0
        quickumls.result_type = "ents"

        concept_term = "dipalmitoyllecithin"
        concept_term += "n"

        text = "Decreased {} content found in lung specimens".format(concept_term)

        doc = quickumls_nlp(text)

        assert len(doc.ents) == 0

        quickumls.quickumls.threshold = original_threshold
        quickumls.quickumls.ss_db.db.threshold = original_threshold

    def test_ensure_match_objects(self, quickumls_nlp):
        """
        Test that an extraction has UmlsMatch objects for it
        """

        quickumls = quickumls_nlp.get_pipe("medspacy_quickumls")
        quickumls.result_type = "ents"

        concept_term = "dipalmitoyllecithin"

        text = "Decreased {} content found in lung specimens".format(concept_term)

        doc = quickumls_nlp(text)

        assert len(doc.ents) == 1

        ent = doc.ents[0]

        assert len(ent._.umls_matches) > 0

        match_object = list(ent._.umls_matches)[0]

        assert match_object.cui.startswith("C")
