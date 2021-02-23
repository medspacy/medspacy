import pytest
import tempfile

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
        rule = "forward"
        item = ConTextRule(literal, category, rule)
        assert item.category == "DEFINITE_NEGATED_EXISTENCE"

    def test_context_item_rule_upper(self):
        """Test that a ConTextRule direction is always upper"""
        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "forward"
        item = ConTextRule(literal, category, rule)
        assert item.direction == "FORWARD"

    def test_rule_value_error(self):
        """Test that ConTextRule raises a ValueError if an invalid direction is passed in."""
        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "asdf"
        with pytest.raises(ValueError):
            ConTextRule(literal, category, rule)

    def test_metadata(self):
        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "forward"
        meta = {"comment": "This is a comment."}
        item = ConTextRule(literal, category, rule, metadata=meta)
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

    def test_to_json(self):
        import json, os

        dname = os.path.join(tmpdirname.name, "tmp_test_modifiers.json")

        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "forward"
        item = ConTextRule(literal, category, rule)
        ConTextRule.to_json([item], dname)


        with open(dname) as f:
            data = json.load(f)
        assert "context_rules" in data
        assert len(data["context_rules"]) == 1
        item = data["context_rules"][0]
        for key in ["literal", "category", "direction"]:
            assert key in item

        #os.remove("test_modifiers.json")

    def test_default_terminate(self):
        item = ConTextRule("no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by=None)
        assert item.terminated_by == set()

    def test_custom_terminate(self):
        item = ConTextRule("no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by={"POSITIVE_EXISTENCE"})
        assert item.terminated_by == {"POSITIVE_EXISTENCE"}

    def test_deprecated_context_item_throws_error(self):
        with pytest.raises(NotImplementedError) as exception_info:
            # This should fail because context_item throws a NotImplementedError
            from medspacy.context import ConTextItem
            ConTextItem()
        exception_info.match(
            "ConTextItem has been deprecated and replaced with ConTextRule."
        )

    def test_deprecated_rule_argument_raises_warrning(self):
        with pytest.warns(DeprecationWarning) as warning_info:
            ConTextRule("no evidence of", "NEGATED_EXISTENCE", rule="FORWARD")
        assert "The 'rule' argument from ConTextItem has been replaced with 'direction'" in warning_info[0].message.args[0]

    def test_deprecated_rule_attribute_raises_warrning(self):
        with pytest.warns(DeprecationWarning) as warning_info:
            rule = ConTextRule("no evidence of", "NEGATED_EXISTENCE")
            rule.rule
        assert "The 'rule' attribute has been replaced with 'direction'." in warning_info[0].message.args[0]



@pytest.fixture
def from_json_file():
    import json, os

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
