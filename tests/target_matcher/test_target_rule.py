import spacy
import warnings
import pytest

import tempfile

tmpdirname = tempfile.TemporaryDirectory()

from medspacy.target_matcher import TargetRule
from medspacy.common.base_rule import BaseRule


class TestTargetRule:
    def test_initiate(self):
        assert TargetRule("pneumonia", "CONDITION")

    def test_inherits_from_base_rule(self):
        rule = TargetRule("pneumonia", "CONDITION")
        assert isinstance(rule, BaseRule)

    def test_to_json(self):
        import json, os

        dname = os.path.join(tmpdirname.name, "test_target_rules.json")

        literal = "pneumonia"
        category = "CONDITION"
        item = TargetRule(literal, category)
        TargetRule.to_json([item], dname)

        with open(dname) as f:
            data = json.load(f)
        assert "target_rules" in data
        assert len(data["target_rules"]) == 1
        rule_dict = data["target_rules"][0]
        for key in ["literal", "category"]:
            assert key in rule_dict

    def test_from_dict(self):
        d = dict(
            literal="pneumonia", category="CONDITION"
        )
        assert TargetRule.from_dict(d)

    def test_from_dict_error(self):
        d = dict(
            literal="pneumonia",
            category="CONDITION",
            invalid="this is an invalid key",
        )
        with pytest.raises(ValueError):
            TargetRule.from_dict(d)

    def test_from_json(self, from_json_file):
        assert TargetRule.from_json(from_json_file)

@pytest.fixture
def from_json_file():
    import json, os

    json_filepath = os.path.join(tmpdirname.name, "test_targets.json")

    item_data = [
        {
            "literal": "pneumonia",
            "category": "CONDITION",
        },
        {
            "literal": "breast cancer",
            "category": "CONDITION",
            "pattern": [{"LOWER": "breast"}, {"LOWER": "cancer"}],
        },
        {
            "literal": "breast cancer",
            "category": "CONDITION",
            "pattern": "breast ca(ncer)?",
        },
    ]

    # Save dicts to a temporary file
    with open(json_filepath, "w") as f:
        json.dump({"target_rules": item_data}, f)

    yield json_filepath
    # os.remove(json_filepath)