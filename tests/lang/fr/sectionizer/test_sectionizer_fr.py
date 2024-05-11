import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
import json

import spacy
import warnings
import pytest

from os import path
from pathlib import Path

import medspacy
from medspacy.section_detection import Sectionizer
from medspacy.section_detection import SectionRule

LANGUAGE_CODE = 'fr'

nlp = spacy.blank(LANGUAGE_CODE)


class TestSectionizerFR:
    def test_initiate(self):
        assert Sectionizer(nlp, language_code = LANGUAGE_CODE)

    def test_initiate_no_patterns(self):
        assert Sectionizer(nlp, language_code = LANGUAGE_CODE,
        rules=None)

    def test_doc_attributes(self):
        sectionizer = Sectionizer(nlp, language_code = LANGUAGE_CODE)

        doc = nlp("Examen physique: Normale")
        sectionizer(doc)

        assert len(doc._.sections)
        assert len(doc._.section_categories)
        assert len(doc._.section_titles)
        assert len(doc._.section_spans)
        assert len(doc._.section_bodies)

    def test_token_attributes(self):
        sectionizer = Sectionizer(nlp, language_code = LANGUAGE_CODE)
        doc = nlp("Examen physique: Normale")
        sectionizer(doc)

        token = doc[-1]

        assert token._.section
        assert len(token._.section_category)
        assert len(token._.section_title)
        assert len(token._.section_span)
        assert len(token._.section_body)
        assert token._.section_rule

    def test_section(self):
        sectionizer = Sectionizer(nlp, language_code = LANGUAGE_CODE)

        doc = nlp("Examen physique: Normale")
        sectionizer(doc)

        section = doc._.sections[0]
        assert section.category == "physical_exam"
        assert doc[section.section_span[0] : section.section_span[1]] == doc[0:]
        assert doc[section.title_span[0] : section.title_span[1]] == doc[0:-1]
        assert doc[section.body_span[0] : section.body_span[1]] == doc[-1:]
        assert section.parent is None
        assert section.rule
