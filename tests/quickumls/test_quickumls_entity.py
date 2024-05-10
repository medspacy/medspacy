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

from medspacy.util import get_quickumls_demo_dir

MEDSPACY_DEFAULT_SPAN_GROUP_NAME = "medspacy_spans"


class TestQuickUMLSEntity:

    # @pytest.mark.skip(reason="quickumls not enabled for spacy v3")
    def test_initialize_pipeline(self):
        """
        Test that a pipeline with a QuickUMLS component can be loaded in medpacy
        """

        # allow default QuickUMLS (very small sample data) to be loaded
        nlp = medspacy.load(medspacy_enable=["medspacy_quickumls"])
        assert nlp

        quickumls = nlp.get_pipe("medspacy_quickumls")
        assert quickumls
        # this is a member of the QuickUMLS algorithm inside the component
        assert quickumls.quickumls
        # Check that the simstring database exists
        assert quickumls.quickumls.ss_db

    # @pytest.mark.skip(reason="quickumls not enabled for spacy v3")
    def test_quickumls_extractions(self):
        """
        Test that extractions can be performed using the very small (<100 concept) UMLS sample resources
        """

        # allow default QuickUMLS (very small sample data) to be loaded
        nlp = medspacy.load(medspacy_enable=["medspacy_quickumls"])
        quickumls = nlp.get_pipe("medspacy_quickumls")

        # TODO -- Consider moving this and other extraction tests to separate tests from loading
        doc = nlp("Decreased dipalmitoyllecithin content found in lung specimens")

        assert len(doc.ents) == 1

        entity_spans = [ent.text for ent in doc.ents]

        assert "dipalmitoyllecithin" in entity_spans

    def test_min_similarity_threshold(self):
        """
        Test that an extraction is NOT made if we set our matching to be perfect matching (100% similarity)
        and we have a typo
        """

        # allow default QuickUMLS (very small sample data) to be loaded
        nlp = spacy.blank("en")

        nlp.add_pipe(
            "medspacy_quickumls",
            config={"threshold": 1.0, "quickumls_fp": get_quickumls_demo_dir("en")},
        )

        concept_term = "dipalmitoyllecithin"
        # Let's turn this into a typo which will no longer match...
        concept_term += "n"

        text = "Decreased {} content found in lung specimens".format(concept_term)

        doc = nlp(text)

        assert len(doc.ents) == 0

    def test_ensure_match_objects(self):
        """
        Test that an extraction has UmlsMatch objects for it
        """

        # allow default QuickUMLS (very small sample data) to be loaded
        nlp = spacy.blank("en")

        nlp.add_pipe(
            "medspacy_quickumls", config={"quickumls_fp": get_quickumls_demo_dir("en")}
        )

        concept_term = "dipalmitoyllecithin"

        text = "Decreased {} content found in lung specimens".format(concept_term)

        doc = nlp(text)

        assert len(doc.ents) == 1

        ent = doc.ents[0]

        assert len(ent._.umls_matches) > 0

        # make sure that we have a reasonable looking CUI
        match_object = list(ent._.umls_matches)[0]

        assert match_object.cui.startswith("C")
