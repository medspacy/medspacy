import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
import spacy
import warnings

import os
from pathlib import Path

from medspacy.common import BaseRule
from medspacy.section_detection import SectionRule

nlp = spacy.load("en_core_web_sm")


class TestSectionizer:
    def test_initialize(self):
        assert SectionRule("title", "literal")

    def test_read_json(self):
        rules_path = os.path.join(
            Path(__file__).resolve().parents[2], "resources", "section_patterns.json"
        )
        rules = SectionRule.from_json(rules_path)
        assert rules
        for rule in rules:
            assert isinstance(rule, SectionRule)
            assert isinstance(rule, BaseRule)

    def test_max_scope(self):
        rule = SectionRule(
            category="past_medical_history",
            literal="Past Medical History:",
            max_scope=100,
        )
        assert rule.max_scope == 100
