import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
import spacy
from spacy.language import Language
from spacy.tokens import Span, Doc
import medspacy

from medspacy.context import ConText
from medspacy.context import ConTextRule

import pytest
import os
from pathlib import Path

nlp = spacy.load("en_core_web_sm")


class TestConText:
    def test_initiate(self):
        assert ConText(nlp)

    def test_default_patterns(self):
        """Test that default rules are loaded"""
        context = ConText(nlp)
        assert context.rules

    def test_empty_patterns(self):
        """Test that no rules are loaded"""
        context = ConText(nlp, rules=None)
        assert not context.rules

    def test_custom_patterns_json(self):
        """Test that rules are loaded from a json"""
        filepath = os.path.join(
            Path(__file__).resolve().parents[2], "resources", "en", "context_rules.json"
        )
        context = ConText(nlp, rules=filepath)
        assert context.rules

    def test_call(self):
        doc = nlp("Pulmonary embolism has been ruled out.")
        context = ConText(nlp)
        doc = context(doc)
        assert isinstance(doc, spacy.tokens.doc.Doc)

    def test_registers_attributes(self):
        """Test that the default ConText attributes are set on ."""
        doc = nlp("There is consolidation.")
        doc.ents = (Span(doc, 2, 3, "CONDITION"),)
        context = ConText(nlp)
        doc = context(doc)
        assert hasattr(doc._, "context_graph")
        assert hasattr(doc.ents[0]._, "modifiers")

    def test_registers_context_attributes(self):
        """Test that the additional attributes such as 'is_negated' are registered on spaCy spans."""
        doc = nlp("This is a span.")
        context = ConText(nlp, span_attrs="default", rules=None)
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
        context = ConText(nlp, rules=None)
        ent = Span(doc, 5, 6, "CONDITION")
        doc.ents = (ent,)
        context(doc)
        for attr_name in [
            "is_negated",
            "is_uncertain",
            "is_historical",
            "is_hypothetical",
            "is_family",
        ]:
            assert getattr(doc.ents[0]._, attr_name) is False

    def test_is_negated(self):
        doc = nlp("There is no evidence of pneumonia.")
        context = ConText(nlp, span_attrs="default", rules=None)
        rules = [
            ConTextRule("no evidence of", "NEGATED_EXISTENCE", direction="forward")
        ]
        context.add(rules)
        doc.ents = (Span(doc, 5, 6, "CONDITION"),)
        context(doc)

        assert doc.ents[0]._.is_negated is True

    def test_is_historical(self):
        doc = nlp("History of pneumonia.")
        context = ConText(nlp, span_attrs="default", rules=None)
        rules = [ConTextRule("history of", "HISTORICAL", direction="forward")]
        context.add(rules)
        doc.ents = (Span(doc, 2, 3, "CONDITION"),)
        context(doc)

        assert doc.ents[0]._.is_historical is True

    def test_is_family(self):
        doc = nlp("Family history of breast cancer.")
        context = ConText(nlp, span_attrs="default", rules=None)
        rules = [ConTextRule("family history of", "FAMILY", direction="forward")]
        context.add(rules)
        doc.ents = (Span(doc, 3, 5, "CONDITION"),)
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
            ConText(nlp, span_attrs=custom_attrs)

    def test_custom_attributes_mapping(self):
        custom_attrs = {
            "NEGATED_EXISTENCE": {"is_negated": True},
        }
        try:
            Span.set_extension("is_negated", default=False)
        except:
            pass
        context = ConText(nlp, span_attrs=custom_attrs)
        assert context.context_attributes_mapping == custom_attrs

    def test_custom_attributes_value1(self):
        custom_attrs = {
            "NEGATED_EXISTENCE": {"is_negated": True},
        }
        try:
            Span.set_extension("is_negated", default=False)
        except:
            pass
        context = ConText(nlp, span_attrs=custom_attrs)
        context.add([ConTextRule("no evidence of", "NEGATED_EXISTENCE", "FORWARD")])
        doc = nlp("There is no evidence of pneumonia.")
        doc.ents = (Span(doc, 5, 6, "CONDITION"),)
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
        context = ConText(nlp, span_attrs=custom_attrs)
        context.add(
            [ConTextRule("no evidence of", "DEFINITE_NEGATED_EXISTENCE", "FORWARD")]
        )
        doc = nlp("There is no evidence of pneumonia.")
        doc.ents = (Span(doc, 5, 6, "CONDITION"),)
        context(doc)

        assert doc.ents[0]._.is_family is False

    def test_simple_callback(self, capsys):
        context = ConText(nlp, rules=None)

        def simple_callback(matcher, doc, i, matches):
            match_id, start, end = matches[i]
            span = doc[start:end]
            print("Matched on span:", span)

        context.add(
            [
                ConTextRule(
                    "no evidence of",
                    "NEGATED_EXISTENCE",
                    direction="FORWARD",
                    on_match=simple_callback,
                )
            ]
        )

        doc = nlp("There is no evidence of pneumonia.")
        context(doc)
        captured = capsys.readouterr()
        assert captured.out == "Matched on span: no evidence of\n"

    def test_global_allowed_types1(self):
        """Check that if the ConText has allowed_types defined
        and a ConTextRule does not, the ConTextRule will receive the component's
        value.
        """
        context = ConText(nlp, rules=None, allowed_types={"PROBLEM"})
        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", allowed_types=None
        )
        context.add([rule])
        assert rule.allowed_types == {"PROBLEM"}

    def test_global_allowed_types2(self):
        """Check that if the ConText does not have allowed_types defined
        and a ConTextRule does, the ConTextRule will not receive the component's
        value.
        """
        context = ConText(nlp, rules=None, allowed_types=None)
        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", allowed_types={"PROBLEM"}
        )
        context.add([rule])
        assert rule.allowed_types == {"PROBLEM"}

    def test_global_allowed_types3(self):
        """Check that if both the ConText and a ConTextRule have allowed_types defined,
        the ConTextRule will not receive the component's value.
        """
        context = ConText(nlp, rules=None, allowed_types={"TREATMENT"})
        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", allowed_types={"PROBLEM"}
        )
        context.add([rule])
        assert rule.allowed_types == {"PROBLEM"}

    def test_context_modifier_termination(self):
        context = ConText(
            nlp,
            rules=None,
            terminating_types={
                "NEGATED_EXISTENCE": ["POSITIVE_EXISTENCE", "UNCERTAIN"]
            },
        )
        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by=None
        )
        context.add([rule])
        assert rule.terminated_by == {"POSITIVE_EXISTENCE", "UNCERTAIN"}

    def test_rule_modifier_termination(self):
        context = ConText(nlp, rules=None, terminating_types=None)
        rule = ConTextRule(
            "no evidence of",
            "NEGATED_EXISTENCE",
            "FORWARD",
            terminated_by={"POSITIVE_EXISTENCE", "UNCERTAIN"},
        )
        context.add([rule])
        assert rule.terminated_by == {"POSITIVE_EXISTENCE", "UNCERTAIN"}

    def test_null_modifier_termination(self):
        context = ConText(nlp, rules=None, terminating_types=None)
        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", "FORWARD", terminated_by=None
        )
        context.add([rule])
        assert rule.terminated_by == set()

    def test_on_modifies_true(self):
        def on_modifies(target, modifier, span_between):
            return True

        context = ConText(nlp, rules=None)
        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", on_modifies=on_modifies
        )
        context.add([rule])
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (Span(doc, 5, 6, "CONDITION"), Span(doc, 7, 8, "CONDITION"))
        context(doc)

        for ent in doc.ents:
            assert len(ent._.modifiers) == 1

    def test_on_modifies_false(self):
        def on_modifies(target, modifier, span_between):
            return False

        context = ConText(nlp, rules=None)
        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", on_modifies=on_modifies
        )
        context.add([rule])
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (Span(doc, 5, 6, "CONDITION"), Span(doc, 7, 8, "CONDITION"))
        context(doc)

        for ent in doc.ents:
            assert len(ent._.modifiers) == 0

    def test_pseudo_modifier(self):
        rules = [
            ConTextRule("negative", "NEGATED_EXISTENCE"),
            ConTextRule(
                "negative attitude", "PSEUDO_NEGATED_EXISTENCE", direction="PSEUDO"
            ),
        ]
        context = ConText(nlp, rules=None)
        context.add(rules)

        doc = nlp("She has a negative attitude about her treatment.")
        doc.ents = (Span(doc, 7, 8, "CONDITION"),)
        context(doc)

        assert len(doc.ents[0]._.modifiers) == 0
        assert len(doc._.context_graph.modifiers) == 1
        assert doc._.context_graph.modifiers[0].category == "PSEUDO_NEGATED_EXISTENCE"

    def test_max_scope(self):
        nlp_no_sents = spacy.blank("en")
        context = ConText(nlp_no_sents, max_scope=1)
        doc = nlp_no_sents("There is no evidence of pneumonia or chf.")
        doc.ents = (Span(doc, 5, 6, "CONDITION"), Span(doc, 7, 8, "CONDITION"))
        context(doc)
        assert doc.ents[0]._.is_negated is True
        assert doc.ents[1]._.is_negated is False

    def test_regex_pattern(self):
        rules = [
            ConTextRule(
                "no history of",
                "NEGATED_EXISTENCE",
                direction="FORWARD",
                pattern="no (history|hx) of",
            ),
        ]
        context = ConText(nlp, rules=None)
        context.add(rules)

        doc = nlp("No history of afib. No hx of MI.")
        context(doc)
        assert len(doc._.context_graph.modifiers) == 2

    def test_prune(self):
        rules = [
            ConTextRule("history of", "HISTORICAL", direction="FORWARD"),
            ConTextRule("no history of", "NEGATED_EXISTENCE", direction="FORWARD"),
        ]
        context = ConText(nlp, rules=None, prune_on_modifier_overlap=True)
        context.add(rules)

        doc = nlp("No history of afib.")
        context(doc)

        assert len(doc._.context_graph.modifiers) == 1
        modifier = doc._.context_graph.modifiers[0]
        span = modifier.modifier_span
        assert doc[span[0] : span[1]].text.lower() == "no history of"

    def test_prune_false(self):
        rules = [
            ConTextRule("history of", "HISTORICAL", direction="FORWARD"),
            ConTextRule("no history of", "NEGATED_EXISTENCE", direction="FORWARD"),
        ]
        context = ConText(nlp, rules=None, prune_on_modifier_overlap=False)
        context.add(rules)

        doc = nlp("No history of afib.")
        context(doc)

        assert len(doc._.context_graph.modifiers) == 2

    def test_non_entity_input(self):
        rules = [
            ConTextRule("history of", "HISTORICAL", direction="FORWARD"),
        ]
        context = ConText(nlp, rules=None)
        context.add(rules)

        doc = nlp("Patient has a history of diabetes and history of renal failiure")
        Doc.set_extension("my_custom_spans", default=[], force=True)
        doc._.my_custom_spans = [doc[-6:-4], doc[-2:]]
        context(doc, "my_custom_spans")
        for span in doc._.my_custom_spans:
            assert span._.is_historical
        Doc.remove_extension("my_custom_spans")

    def test_allowed_types(self):
        doc = nlp("She is not prescribed any beta blockers for her hypertension.")
        # Manually define entities
        medication_ent = Span(doc, 5, 7, "MEDICATION")
        condition_ent = Span(doc, 9, 10, "CONDITION")
        doc.ents = (medication_ent, condition_ent)

        rule = ConTextRule(
            "not prescribed",
            "NEGATED_EXISTENCE",
            direction="FORWARD",
            allowed_types={"MEDICATION"},
        )

        context = ConText(nlp, rules=None)
        context.add(rule)
        doc = context(doc)

        assert len(doc._.context_graph.edges) == 1

    # def test_non_entity_input_non_iterable(self): # not sure what this is testing
    #     rules = [
    #         ConTextRule("history of", "HISTORICAL", direction="FORWARD"),
    #     ]
    #     context = ConText(nlp, rules=None)
    #     context.add(rules)
    #
    #     doc = nlp("Patient has a history of diabetes and history of renal failiure")
    #     Doc.set_extension("my_custom_spans", default=[], force=True)
    #     doc._.my_custom_spans = doc[-6:-4]
    #     with pytest.raises(TypeError) as exception_info:
    #         context(doc, "my_custom_spans")
    #         assert exception_info.match(
    #             "argument of type 'spacy.tokens.token.Token' is not iterable"
    #         )
    #     Doc.remove_extension("my_custom_spans")

    def test_context_component_as_part_of_pipeline(self):
        @Language.factory("custom_span_setter")
        class CustomSpanSetterForTesting:
            def __init__(self, nlp, name="custom_span_setter"):
                self.nlp = nlp
                self.name = name
                if not Doc.has_extension("my_custom_spans"):
                    Doc.set_extension("my_custom_spans", default=[], force=True)

            def __call__(self, doc):
                doc._.my_custom_spans = [doc[-6:-4], doc[-2:]]
                return doc

        nlp.add_pipe("custom_span_setter")
        nlp.add_pipe("medspacy_context", config={"rules": None})
        nlp.get_pipe("medspacy_context").add(
            [
                ConTextRule("history of", "HISTORICAL", direction="FORWARD"),
            ]
        )
        doc = nlp(
            "Patient has a history of diabetes and history of renal failiure",
            component_cfg={"medspacy_context": {"targets": "my_custom_spans"}},
        )
        for span in doc._.my_custom_spans:
            assert span._.is_historical
        Doc.remove_extension("my_custom_spans")
        nlp.remove_pipe("custom_span_setter")
        nlp.remove_pipe("medspacy_context")
