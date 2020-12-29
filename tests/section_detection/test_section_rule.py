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

    def test_patterns_to_rules(self):
        from medspacy.section_detection import section_patterns_to_rules
        patterns = [
            {"section_title": "past_medical_history", "pattern": "Past Medical History"},
            {
                "section_title": "assessment_and_plan",
                "pattern":
                    [{"LOWER": "assessment"}, {"LOWER": "and"}, {"LOWER": "plan"}]
            }
        ]

        rules = section_patterns_to_rules(patterns)
        assert isinstance(rules[0], SectionRule)
        assert rules[0].category == "past_medical_history"
        assert rules[0].literal == "Past Medical History"
        assert rules[0].pattern is None

        assert isinstance(rules[1], SectionRule)
        assert rules[1].category == "assessment_and_plan"
        assert rules[1].literal == str([{"LOWER": "assessment"}, {"LOWER": "and"}, {"LOWER": "plan"}])
        assert rules[1].pattern == [{"LOWER": "assessment"}, {"LOWER": "and"}, {"LOWER": "plan"}]
