import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
import spacy
from spacy.language import Language
from spacy.tokens import Span, Doc
import medspacy

from medspacy.context import ConText
from medspacy.context import ConTextRule

import pytest
import os
from pathlib import Path

nlp = spacy.blank("nl")
nlp.add_pipe('sentencizer')

LANGUAGE_CODE = 'nl'

class TestConTextNL:
    def test_custom_patterns_json(self):
        """Test that rules are loaded from a json"""

        context = ConText(nlp, language_code=LANGUAGE_CODE)
        assert context.rules

    def test_call(self):
        doc = nlp("Patiënt heeft geen kanker")
        context = ConText(nlp, language_code=LANGUAGE_CODE)
        doc = context(doc)
        assert isinstance(doc, spacy.tokens.doc.Doc)

    def test_is_negated(self):
        doc = nlp("Patiënt heeft geen kanker")
        context = ConText(nlp, language_code=LANGUAGE_CODE)
        doc.ents = (Span(doc, 3, 4, "CONDITION"),)
        context(doc)

        assert doc.ents[0]._.is_negated is True

