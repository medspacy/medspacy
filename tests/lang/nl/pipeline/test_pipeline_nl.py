import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())

import spacy
import warnings
import pytest

import medspacy

from medspacy.target_matcher import TargetMatcher, TargetRule

LANGUAGE_CODE = 'nl'


class TestPipelineDE:
    def test_create_pipeline(self):
        nlp = medspacy.load(language_code = LANGUAGE_CODE)

        assert nlp

    def test_default_components(self):
        nlp = medspacy.load(language_code = LANGUAGE_CODE, enable = ['medspacy_target_matcher'])

        matcher = nlp.get_pipe('medspacy_target_matcher')
        matcher.add([TargetRule("kanker", "CONDITION", pattern=[{"LOWER": "kanker"}])])

        doc = nlp("""Patiënt heeft geen kanker""")

        assert doc

        assert doc.ents[0]._.is_negated is True
