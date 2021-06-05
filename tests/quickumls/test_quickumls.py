import spacy
import warnings
from sys import platform
import pytest

import medspacy

class TestQuickUMLS:

    @staticmethod
    def can_test_quickumls():
        if platform.startswith("win"):
            # we're done here for now...
            return False

        return True

    # @pytest.mark.skip(reason="quickumls not enabled for spacy v3")
    def test_initialize_pipeline(self):
        """
        Test that a pipeline with a QuickUMLS component can be loaded in medpacy
        NOTE: Currently this is only available by default in Linux and MacOS
            Windows requires additional steps, but this will test capability on Windows
            if these manual steps are followed
        """

        # let's make sure that this pipe has been initialized
        # At least for MacOS and Linux which are currently supported...
        if not TestQuickUMLS.can_test_quickumls():
            return

        # allow default QuickUMLS (very small sample data) to be loaded
        nlp = medspacy.load(enable=["quickumls"])
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

        # let's make sure that this pipe has been initialized
        # At least for MacOS and Linux which are currently supported...
        if not TestQuickUMLS.can_test_quickumls():
            return

        # allow default QuickUMLS (very small sample data) to be loaded
        nlp = medspacy.load(enable=["quickumls"])
        quickumls = nlp.get_pipe("medspacy_quickumls")

        # TODO -- Consider moving this and other extraction tests to separate tests from loading
        doc = nlp('Decreased dipalmitoyllecithin content found in lung specimens')

        assert len(doc.ents) == 1

        entity_spans = [ent.text for ent in doc.ents]

        assert 'dipalmitoyllecithin' in entity_spans