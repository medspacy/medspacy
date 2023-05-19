import tempfile

import pytest

tmpdirname = tempfile.TemporaryDirectory()

from medspacy.context import ConTextRule
from medspacy.common.base_rule import BaseRule


class TestItemData:
    def test_instantiate1(self):
        literal = "no evidence of"
        category = "DEFINITE_NEGATED_EXISTENCE"
        rule = "forward"
        assert ConTextRule(literal, category, rule)

    def test_context_item_inherits_base_rule(self):
        literal = "no evidence of"
        category = "DEFINITE_NEGATED_EXISTENCE"
        rule = "forward"
        item = ConTextRule(literal, category, rule)
        assert isinstance(item, BaseRule)

    def test_context_item_category_upper(self):
        """Test that a ConTextRule category is always upper"""
        literal = "no evidence of"
        category = "definite_negated_existence"
        direction = "forward"
        item = ConTextRule(literal, category, direction=direction)
        assert item.category == "DEFINITE_NEGATED_EXISTENCE"

    def test_context_item_rule_upper(self):
        """Test that a ConTextRule direction is always upper"""
        literal = "no evidence of"
        category = "definite_negated_existence"
        direction = "forward"
        item = ConTextRule(literal, category, direction=direction)
        assert item.direction == "FORWARD"

    def test_rule_value_error(self):
        """Test that ConTextRule raises a ValueError if an invalid direction is passed in."""
        literal = "no evidence of"
        category = "definite_negated_existence"
        direction = "asdf"
        with pytest.raises(ValueError):
            ConTextRule(literal, category, direction=direction)

    def test_metadata(self):
        literal = "no evidence of"
        category = "definite_negated_existence"
        direction = "forward"
        meta = {"comment": "This is a comment."}
        item = ConTextRule(literal, category, direction=direction, metadata=meta)
        assert item.metadata

    def test_from_dict(self):
        d = dict(
            literal="reason for examination", category="INDICATION", direction="FORWARD"
        )
        assert ConTextRule.from_dict(d)

    def test_from_dict_error(self):
        d = dict(
            literal="reason for examination",
            category="INDICATION",
            direction="FORWARD",
            invalid="this is an invalid key",
        )
        with pytest.raises(ValueError):
            ConTextRule.from_dict(d)

    def test_from_json(self, from_json_file):
        assert ConTextRule.from_json(from_json_file)

    def test_to_dict(self):
        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "forward"
        item = ConTextRule(literal, category, rule)
        assert isinstance(item.to_dict(), dict)

    def test_default_terminate(self):
        item = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by=None
        )
        assert item.terminated_by == set()

    def test_custom_terminate(self):
        item = ConTextRule(
            "no evidence of",
            "NEGATED_EXISTENCE",
            "FORWARD",
            terminated_by={"POSITIVE_EXISTENCE"},
        )
        assert item.terminated_by == {"POSITIVE_EXISTENCE"}

    def test_to_json(self):
       import json, os

       dname = os.path.join(tmpdirname.name, "test_modifiers.json")

       item_data = [
           {
               "literal": "are ruled out",
               "category": "DEFINITE_NEGATED_EXISTENCE",
               "pattern": None,
               "direction": "backward",
           },
           {
               "literal": "is negative",
               "category": "DEFINITE_NEGATED_EXISTENCE",
               "pattern": [{"LEMMA": "be"}, {"LOWER": "negative"}],
               "direction": "backward",
               "allowed_types": ["A_TYPE"],
           },
        ]

       rules = [ConTextRule.from_dict(d) for d in item_data]
       ConTextRule.to_json(rules, dname)

       with open(dname) as f:
           data = json.load(f)
       assert "context_rules" in data
       assert len(data["context_rules"]) == 2
       rule_dict = data["context_rules"][0]
       assert set(rule_dict.keys()) == {'literal', 'category', 'direction'}
       rule_dict = data["context_rules"][1]
       assert set(rule_dict.keys()) == {'literal', 'pattern', 'category', 'direction', 'allowed_types'}

@pytest.fixture
def from_json_file():
    import json
    import os

    json_filepath = os.path.join(tmpdirname.name, "test_modifiers.json")

    item_data = [
        {
            "literal": "are ruled out",
            "category": "DEFINITE_NEGATED_EXISTENCE",
            "pattern": None,
            "direction": "backward",
        },
        {
            "literal": "is negative",
            "category": "DEFINITE_NEGATED_EXISTENCE",
            "pattern": [{"LEMMA": "be"}, {"LOWER": "negative"}],
            "direction": "backward",
        },
    ]

    # Save dicts to a temporary file
    with open(json_filepath, "w") as f:
        json.dump({"context_rules": item_data}, f)

    yield json_filepath
    # os.remove(json_filepath)
