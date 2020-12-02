import pytest
import tempfile

tmpdirname = tempfile.TemporaryDirectory()

from medspacy.context import ConTextItem
from medspacy.common.base_rule import BaseRule


class TestItemData:
    def test_instantiate1(self):
        literal = "no evidence of"
        category = "DEFINITE_NEGATED_EXISTENCE"
        rule = "forward"
        assert ConTextItem(literal, category, rule)

    def test_context_item_inherits_base_rule(self):
        literal = "no evidence of"
        category = "DEFINITE_NEGATED_EXISTENCE"
        rule = "forward"
        item = ConTextItem(literal, category, rule)
        assert isinstance(item, BaseRule)

    def test_context_item_category_upper(self):
        """Test that a ConTextItem category is always upper"""
        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "forward"
        item = ConTextItem(literal, category, rule)
        assert item.category == "DEFINITE_NEGATED_EXISTENCE"

    def test_context_item_rule_upper(self):
        """Test that a ConTextItem rule is always upper"""
        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "forward"
        item = ConTextItem(literal, category, rule)
        assert item.rule == "FORWARD"

    def test_rule_value_error(self):
        """Test that ConTextItem raises a ValueError if an invalid rule is passed in."""
        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "asdf"
        with pytest.raises(ValueError):
            ConTextItem(literal, category, rule)

    def test_metadata(self):
        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "forward"
        meta = {"comment": "This is a comment."}
        item = ConTextItem(literal, category, rule, metadata=meta)
        assert item.metadata

    def test_from_dict(self):
        d = dict(
            literal="reason for examination", category="INDICATION", rule="FORWARD"
        )
        assert ConTextItem.from_dict(d)

    def test_from_dict_error(self):
        d = dict(
            literal="reason for examination",
            category="INDICATION",
            rule="FORWARD",
            invalid="this is an invalid key",
        )
        with pytest.raises(ValueError):
            ConTextItem.from_dict(d)

    def test_from_json(self, from_json_file):
        assert ConTextItem.from_json(from_json_file)

    def test_to_dict(self):
        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "forward"
        item = ConTextItem(literal, category, rule)
        assert isinstance(item.to_dict(), dict)

    def test_to_json(self):
        import json, os

        dname = os.path.join(tmpdirname.name, "test_modifiers.json")

        literal = "no evidence of"
        category = "definite_negated_existence"
        rule = "forward"
        item = ConTextItem(literal, category, rule)
        ConTextItem.to_json([item], dname)

        with open(dname) as f:
            data = json.load(f)
        assert "item_data" in data
        assert len(data["item_data"]) == 1
        item = data["item_data"][0]
        for key in ["literal", "category", "rule"]:
            assert key in item

        #os.remove("test_modifiers.json")

    def test_default_terminate(self):
        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by=None)
        assert item.terminated_by == set()

    def test_custom_terminate(self):
        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by={"POSITIVE_EXISTENCE"})
        assert item.terminated_by == {"POSITIVE_EXISTENCE"}


@pytest.fixture
def from_json_file():
    import json, os

    json_filepath = os.path.join(tmpdirname.name, "test_modifiers.json")

    item_data = [
        {
            "literal": "are ruled out",
            "category": "DEFINITE_NEGATED_EXISTENCE",
            "pattern": None,
            "rule": "backward",
        },
        {
            "literal": "is negative",
            "category": "DEFINITE_NEGATED_EXISTENCE",
            "pattern": [{"LEMMA": "be"}, {"LOWER": "negative"}],
            "rule": "backward",
        },
    ]

    # Save dicts to a temporary file
    with open(json_filepath, "w") as f:
        json.dump({"item_data": item_data}, f)

    yield json_filepath
    # os.remove(json_filepath)
