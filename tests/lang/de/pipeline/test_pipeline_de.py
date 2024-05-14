import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())

import spacy
import warnings
import pytest

import medspacy

LANGUAGE_CODE = 'de'


class TestPipelineDE:
    def test_create_pipeline(self):
        nlp = medspacy.load(language_code = LANGUAGE_CODE)

        assert nlp

    def test_default_components(self):
        nlp = medspacy.load(language_code = LANGUAGE_CODE)

        nlp.add_pipe("medspacy_sectionizer", config = {'language_code': LANGUAGE_CODE})

        doc = nlp("""Zusammenfassung des Arztbesuchs

                    Datum des Besuchs: 14. Mai 2024
                    Name des Patienten: burgersmoke""")

        assert doc
        assert len(doc._.sections) > 0
