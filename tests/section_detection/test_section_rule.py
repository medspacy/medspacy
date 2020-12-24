import spacy
import warnings

from medspacy.common import BaseRule
from medspacy.section_detection import SectionRule

nlp = spacy.load("en_core_web_sm")


class TestSectionizer:
    def test_initialize(self):
        assert SectionRule("title", "literal")

    def test_read_json(self):
        rules = SectionRule.from_json("resources/section_patterns.json")
        assert rules
        for rule in rules:
            assert isinstance(rule, SectionRule)
            assert isinstance(rule, BaseRule)
