import spacy
from spacy.tokens import Span

from medspacy.context import ConTextComponent
from medspacy.context import ConTextItem

import pytest
import os

nlp = spacy.load("en_core_web_sm")


class TestConTextComponent:
    def test_initiate(self):
        assert ConTextComponent(nlp)

    def test_default_patterns(self):
        """Test that default rules are loaded"""
        context = ConTextComponent(nlp)
        assert context.item_data

    def test_empty_patterns(self):
        """Test that no rules are loaded"""
        context = ConTextComponent(nlp, rules=None)
        assert not context.item_data

    def test_custom_patterns_json(self):
        """Test that rules are loaded from a json"""
        context = ConTextComponent(
            nlp, rules="other", rule_list=os.path.abspath("resources/context_rules.json")
        )
        assert context.item_data

    def test_custom_patterns_list(self):
        """Test that rules are loaded from a list"""
        item = ConTextItem("evidence of", "DEFINITE_EXISTENCE", "forward")
        context = ConTextComponent(nlp, rules="other", rule_list=[item])
        assert context.item_data

    def test_bad_rules_arg(self):
        with pytest.raises(ValueError):
            ConTextComponent(nlp, rules="not valid")

    def test_bad_rule_list_path(self):
        with pytest.raises(ValueError):
            ConTextComponent(nlp, rules="other", rule_list="not a path")

    def test_bad_rule_list_empty(self):
        with pytest.raises(ValueError):
            ConTextComponent(nlp, rules="other", rule_list=[])

    def test_bad_rule_list_items(self):
        with pytest.raises(ValueError):
            ConTextComponent(nlp, rules="other", rule_list=["list of strings"])

    def test_call(self):
        doc = nlp("Pulmonary embolism has been ruled out.")
        context = ConTextComponent(nlp)
        doc = context(doc)
        assert isinstance(doc, spacy.tokens.doc.Doc)

    def test_registers_attributes(self):
        """Test that the default ConText attributes are set on ."""
        doc = nlp("There is consolidation.")
        doc.ents = (doc[-2:-1],)
        context = ConTextComponent(nlp)
        doc = context(doc)
        assert hasattr(doc._, "context_graph")
        assert hasattr(doc.ents[0]._, "modifiers")

    def test_registers_context_attributes(self):
        """Test that the additional attributes such as
        'is_negated' are registered on spaCy spans.
        """
        doc = nlp("This is a span.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        context(doc)
        span = doc[-2:]
        for attr_name in [
            "is_negated",
            "is_uncertain",
            "is_historical",
            "is_hypothetical",
            "is_family",
        ]:
            assert hasattr(span._, attr_name)

    def test_default_attribute_values(self):
        """Check that default Span attributes have False values without any modifiers."""
        doc = nlp("There is evidence of pneumonia.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        doc.ents = (doc[-2:-1],)
        context(doc)
        for attr_name in [
            "is_negated",
            "is_uncertain",
            "is_historical",
            "is_hypothetical",
            "is_family",
        ]:
            assert getattr(doc.ents[0]._, attr_name) is False

    def test_default_rules_match(self):
        context = ConTextComponent(nlp)
        matcher = context.matcher
        assert matcher(nlp("no evidence of"))

    def test_custom_rules_match(self):
        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", "forward")
        context = ConTextComponent(nlp, rules="other", rule_list=[item])
        matcher = context.phrase_matcher
        assert matcher(nlp("no evidence of"))

    def test_is_negated(self):
        doc = nlp("There is no evidence of pneumonia.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        item_data = [ConTextItem("no evidence of", "NEGATED_EXISTENCE", rule="forward")]
        context.add(item_data)
        doc.ents = (doc[-2:-1],)
        context(doc)

        assert doc.ents[0]._.is_negated is True

    def test_is_historical(self):
        doc = nlp("History of pneumonia.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        item_data = [ConTextItem("history of", "HISTORICAL", rule="forward")]
        context.add(item_data)
        doc.ents = (doc[-2:-1],)
        context(doc)

        assert doc.ents[0]._.is_historical is True

    def test_is_family(self):
        doc = nlp("Family history of breast cancer.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        item_data = [ConTextItem("family history of", "FAMILY", rule="forward")]
        context.add(item_data)
        doc.ents = (doc[-3:-1],)
        context(doc)

        assert doc.ents[0]._.is_family is True

    def test_custom_attribute_error(self):
        """Test that a custom spacy attribute which has not been set
        will throw a ValueError.
        """
        custom_attrs = {
            "FAKE_MODIFIER": {"non_existent_attribute": True},
        }
        with pytest.raises(ValueError):
            ConTextComponent(nlp, add_attrs=custom_attrs)

    def test_custom_attributes_mapping(self):
        custom_attrs = {
            "NEGATED_EXISTENCE": {"is_negated": True},
        }
        try:
            Span.set_extension("is_negated", default=False)
        except:
            pass
        context = ConTextComponent(nlp, add_attrs=custom_attrs)
        assert context.context_attributes_mapping == custom_attrs

    def test_custom_attributes_value1(self):
        custom_attrs = {
            "NEGATED_EXISTENCE": {"is_negated": True},
        }
        try:
            Span.set_extension("is_negated", default=False)
        except:
            pass
        context = ConTextComponent(nlp, add_attrs=custom_attrs)
        context.add([ConTextItem("no evidence of", "NEGATED_EXISTENCE", "FORWARD")])
        doc = nlp("There is no evidence of pneumonia.")
        doc.ents = (doc[-2:-1],)
        context(doc)

        assert doc.ents[0]._.is_negated is True

    def test_custom_attributes_value2(self):
        custom_attrs = {
            "FAMILY": {"is_family": True},
        }
        try:
            Span.set_extension("is_family", default=False)
        except:
            pass
        context = ConTextComponent(nlp, add_attrs=custom_attrs)
        context.add(
            [ConTextItem("no evidence of", "DEFINITE_NEGATED_EXISTENCE", "FORWARD")]
        )
        doc = nlp("There is no evidence of pneumonia.")
        doc.ents = (doc[-2:-1],)
        context(doc)

        assert doc.ents[0]._.is_family is False

    def test_simple_callback(self, capsys):
        context = ConTextComponent(nlp, rules=None)

        def simple_callback(matcher, doc, i, matches):
            match_id, start, end = matches[i]
            span = doc[start:end]
            print("Matched on span:", span)

        context.add(
            [
                ConTextItem(
                    "no evidence of",
                    "NEGATED_EXISTENCE",
                    "FORWARD",
                    on_match=simple_callback,
                )
            ]
        )

        doc = nlp("There is no evidence of pneumonia.")
        context(doc)
        captured = capsys.readouterr()
        assert captured.out == "Matched on span: no evidence of\n"

    def test_global_allowed_types1(self):
        """Check that if the ConTextComponent has allowed_types defined
        and a ConTextItem does not, the ConTextItem will receive the component's
        value.
        """
        context = ConTextComponent(nlp, rules=None, allowed_types={"PROBLEM"})
        item = ConTextItem(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", allowed_types=None
        )
        context.add([item])
        assert item.allowed_types == {"PROBLEM"}

    def test_global_allowed_types2(self):
        """Check that if the ConTextComponent does not have allowed_types defined
        and a ConTextItem does, the ConTextItem will not receive the component's
        value.
        """
        context = ConTextComponent(nlp, rules=None, allowed_types=None)
        item = ConTextItem(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", allowed_types={"PROBLEM"}
        )
        context.add([item])
        assert item.allowed_types == {"PROBLEM"}

    def test_global_allowed_types2(self):
        """Check that if both the ConTextComponent and a ConTextItem have allowed_types defined,
        the ConTextItem will not receive the component's value.
        """
        context = ConTextComponent(nlp, rules=None, allowed_types={"TREATMENT"})
        item = ConTextItem(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", allowed_types={"PROBLEM"}
        )
        context.add([item])
        assert item.allowed_types == {"PROBLEM"}

    def test_context_modifier_termination(self):
        context = ConTextComponent(nlp, rules=None, terminations={"NEGATED_EXISTENCE": ["POSITIVE_EXISTENCE", "UNCERTAIN"]})
        item = ConTextItem(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by=None
        )
        context.add([item])
        assert item.terminated_by == {"POSITIVE_EXISTENCE", "UNCERTAIN"}

    def test_item_modifier_termination(self):
        context = ConTextComponent(nlp, rules=None,
                                   terminations=None)
        item = ConTextItem(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by={"POSITIVE_EXISTENCE", "UNCERTAIN"}
        )
        context.add([item])
        assert item.terminated_by == {"POSITIVE_EXISTENCE", "UNCERTAIN"}

    def test_null_modifier_termination(self):
        context = ConTextComponent(nlp, rules=None,
                                   terminations=None)
        item = ConTextItem(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by=None
        )
        context.add([item])
        assert item.terminated_by == set()

    def test_on_modifies_true(self):
        def on_modifies(target, modifier, span_between):
            return True

        context = ConTextComponent(nlp, rules=None)
        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", on_modifies=on_modifies)
        context.add([item])
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (doc[5:6], doc[7:8])
        context(doc)

        for ent in doc.ents:
            assert len(ent._.modifiers) == 1

    def test_on_modifies_false(self):
        def on_modifies(target, modifier, span_between):
            return False

        context = ConTextComponent(nlp, rules=None)
        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", on_modifies=on_modifies)
        context.add([item])
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (doc[5:6], doc[7:8])
        context(doc)

        for ent in doc.ents:
            assert len(ent._.modifiers) == 0

    def test_pseudo_modifier(self):
        item_data = [
            ConTextItem("negative", "NEGATED_EXISTENCE"),
            ConTextItem("negative attitude", "PSEUDO_NEGATED_EXISTENCE", rule="PSEUDO"),
        ]
        context = ConTextComponent(nlp, rules=None)
        context.add(item_data)

        doc = nlp("She has a negative attitude about her treatment.")
        doc.ents = (doc[-2:-1],)
        context(doc)

        assert len(doc.ents[0]._.modifiers) == 0
        assert len(doc._.context_graph.modifiers) == 1
        assert doc._.context_graph.modifiers[0].category == "PSEUDO_NEGATED_EXISTENCE"

    def test_context_window_no_max_scope_fails(self):
        "Test that if use_context_window is True but max_scope is None, the instantiation will fail"
        with pytest.raises(ValueError) as exception_info:
            context = ConTextComponent(nlp, max_scope=None, use_context_window=True)
        exception_info.match(
            "If 'use_context_window' is True, 'max_scope' must be an integer greater 1, not None"
        )
