import spacy
import warnings

from medspacy.target_matcher import TargetRule
from medspacy.common.base_rule import BaseRule


class TestTargetRule:
    def test_initiate(self):
        assert TargetRule("pneumonia", "CONDITION")

    def test_inherits_from_base_rule(self):
        rule = TargetRule("pneumonia", "CONDITION")
        assert isinstance(rule, BaseRule)