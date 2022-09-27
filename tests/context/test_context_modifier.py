import pytest
import spacy
from spacy.tokens import Span, Doc

from medspacy.context import ConTextRule, ConTextComponent
from medspacy.context.context_modifier import ConTextModifier

nlp = spacy.load("en_core_web_sm")


class TestConTextModifier:
    def create_objects(self):
        doc = nlp("family history of breast cancer but no diabetes. She has afib.")
        rule = ConTextRule("family history of", "FAMILY_HISTORY", direction="FORWARD")
        modifier = ConTextModifier(rule, 0, 3, doc)
        return doc, rule, modifier

    def create_target_type_examples(self):
        doc = nlp("no history of travel to Puerto Rico pneumonia")
        span1 = Span(doc, start=5, end=7, label="TRAVEL")
        span2 = Span(doc, start=7, end=8, label="CONDITION")
        doc.ents = (span1, span2)
        return doc

    def create_num_target_examples(self):
        doc = nlp("Pt with diabetes, pneumonia vs COPD")
        spans = [
            Span(doc, 2, 3, "CONDITION"),
            Span(doc, 4, 5, "CONDITION"),
            Span(doc, 6, 7, "CONDITION"),
        ]
        doc.ents = spans
        return doc

    def create_num_target_examples_no_sent(self):
        doc = nlp.tokenizer("Pt with diabetes, pneumonia vs COPD")
        spans = [
            Span(doc, 2, 3, "CONDITION"),
            Span(doc, 4, 5, "CONDITION"),
            Span(doc, 6, 7, "CONDITION"),
        ]
        doc.ents = spans
        return doc

    def test_init(self):
        assert self.create_objects()

    def test_span(self):
        doc, rule, modifier = self.create_objects()
        span = modifier.modifier_span
        assert doc[span[0] : span[1]] == doc[0:3]

    def test_direction(self):
        doc, rule, modifier = self.create_objects()
        assert modifier.direction == "FORWARD"

    def test_category(self):
        doc, rule, modifier = self.create_objects()
        assert modifier.category == "FAMILY_HISTORY"

    def test_default_scope(self):
        """Test that the scope goes from the end of the modifier phrase
        to the end of the sentence.
        """
        doc, rule, modifier = self.create_objects()
        scope = modifier.scope_span
        assert doc[scope[0] : scope[1]] == doc[3:-4]

    def test_limit_scope_terminate(self):
        """Test that a 'TERMINATE' ConTextModifier limits the scope of the modifier object"""
        doc, rule, modifier = self.create_objects()
        rule2 = ConTextRule("but", "TERMINATE", direction="TERMINATE")
        modifier2 = ConTextModifier(rule2, 2, 4, doc)
        assert modifier.limit_scope(modifier2)

    def test_limit_scope_same_types(self):
        """Test that two modifiers of the same type limit the scope of the first modifier."""
        doc = nlp("no evidence of CHF, neg for pneumonia")
        rule = ConTextRule(
            "no evidence of", "DEFINITE_NEGATED_EXISTENCE", direction="FORWARD"
        )
        rule2 = ConTextRule("neg for", "DEFINITE_NEGATED_EXISTENCE", "FORWARD")
        modifier = ConTextModifier(rule, 0, 3, doc)
        modifier2 = ConTextModifier(rule2, 5, 7, doc)
        assert modifier.limit_scope(modifier2)

    def test_terminate_limit_scope_custom(self):
        """Test that a modifier will be explicitly terminated by a modifier with a category
        in terminated_by."""
        doc = nlp("negative for flu, positive for pneumonia.")
        rule = ConTextRule(
            "negative for",
            "NEGATED_EXISTENCE",
            direction="FORWARD",
            terminated_by={"POSITIVE_EXISTENCE"},
        )
        rule2 = ConTextRule("positive for", "POSITIVE_EXISTENCE", direction="FORWARD")
        modifier = ConTextModifier(rule, 0, 2, doc)
        modifier2 = ConTextModifier(rule2, 4, 6, doc)
        assert modifier.limit_scope(modifier2)

    def test_terminate_limit_scope_custom2(self):
        """Test that a modifier will be explicitly terminated by a modifier with a category in terminated_by."""
        doc = nlp("flu is negative, pneumonia is positive.")
        rule = ConTextRule("negative", "NEGATED_EXISTENCE", direction="BACKWARD")
        rule2 = ConTextRule(
            "positive",
            "POSITIVE_EXISTENCE",
            direction="BACKWARD",
            terminated_by={"NEGATED_EXISTENCE"},
        )
        modifier = ConTextModifier(rule, 2, 3, doc)
        modifier2 = ConTextModifier(rule2, 6, 7, doc)
        assert modifier2.limit_scope(modifier)

    def test_terminate_limit_scope_backward(self):
        """Test that a 'TERMINATE' modifier will limit the scope of a 'BACKWARD' modifier."""
        doc = nlp("Pt has chf but pneumonia is ruled out")
        rule = ConTextRule("is ruled out", "NEGATED_EXISTENCE", direction="BACKWARD")
        modifier = ConTextModifier(rule, 6, 8, doc)

        rule2 = ConTextRule("but", "TERMINATE", direction="TERMINATE")
        modifier2 = ConTextModifier(rule2, 3, 4, doc)
        assert modifier.limit_scope(modifier2)

    def test_terminate_stops_forward_modifier(self):
        context = ConTextComponent(nlp, rules=None)

        rule = ConTextRule("no evidence of", "NEGATED_EXISTENCE", direction="FORWARD")
        rule2 = ConTextRule("but", "TERMINATE", direction="TERMINATE")
        context.add([rule, rule2])
        doc = nlp("No evidence of chf but she has pneumonia.")
        doc.ents = (Span(doc, 3, 4, "PROBLEM"), Span(doc, 7, 8, "PROBLEM"))
        context(doc)
        chf, pneumonia = doc.ents
        assert len(chf._.modifiers) > 0
        assert len(pneumonia._.modifiers) == 0

    def test_terminate_stops_backward_modifier(self):
        context = ConTextComponent(nlp, rules=None)

        rule = ConTextRule("is ruled out", "NEGATED_EXISTENCE", direction="BACKWARD")
        rule2 = ConTextRule("but", "CONJ", direction="TERMINATE")
        context.add([rule, rule2])
        doc = nlp("Pt has chf but pneumonia is ruled out")
        doc.ents = (Span(doc, 2, 3, "PROBLEM"), Span(doc, 4, 5, "PROBLEM"))
        context(doc)
        chf, pneumonia = doc.ents
        assert len(chf._.modifiers) == 0
        assert len(pneumonia._.modifiers) > 0

    def test_no_custom_terminate_stops_forward_modifier(self):
        doc = nlp("negative for flu, positive for pneumonia.")
        context = ConTextComponent(nlp, rules=None)

        rule = ConTextRule(
            "negative for", "NEGATED_EXISTENCE", direction="FORWARD", terminated_by=None
        )
        rule2 = ConTextRule("positive for", "POSITIVE_EXISTENCE", direction="FORWARD")
        context.add([rule, rule2])
        doc.ents = (Span(doc, 2, 3, "PROBLEM"), Span(doc, 6, 7, "PROBLEM"))
        flu, pneumonia = doc.ents
        context(doc)
        assert len(flu._.modifiers) == 1
        assert len(pneumonia._.modifiers) == 2

    def test_custom_terminate_stops_forward_modifier(self):
        doc = nlp("negative for flu, positive for pneumonia.")
        context = ConTextComponent(nlp, rules=None)

        rule = ConTextRule(
            "negative for",
            "NEGATED_EXISTENCE",
            direction="FORWARD",
            terminated_by={"POSITIVE_EXISTENCE"},
        )
        rule2 = ConTextRule("positive for", "POSITIVE_EXISTENCE", direction="FORWARD")
        context.add([rule, rule2])
        doc.ents = (Span(doc, 2, 3, "PROBLEM"), Span(doc, 6, 7, "PROBLEM"))
        flu, pneumonia = doc.ents
        context(doc)
        assert len(flu._.modifiers) == 1
        assert len(pneumonia._.modifiers) == 1

    def test_no_limit_scope_same_category_different_allowed_types(self):
        """Test that a two ConTextModifiers of the same type but with different
        allowed types does not limits the scope of the modifier object.
        """
        doc = nlp("no history of travel to Puerto Rico, neg for pneumonia")

        rule = ConTextRule(
            "no history of",
            "DEFINITE_NEGATED_EXISTENCE",
            direction="FORWARD",
            allowed_types={"TRAVEL"},
        )
        rule2 = ConTextRule(
            "neg for",
            "DEFINITE_NEGATED_EXISTENCE",
            direction="FORWARD",
            allowed_types={"CONDITION"},
        )
        modifier = ConTextModifier(rule, 0, 3, doc)
        modifier2 = ConTextModifier(rule2, 8, 10, doc)
        assert not modifier.limit_scope(modifier2)

    def test_set_scope_fails_no_sentences(self):
        """Test that setting the scope fails if sentence boundaries haven't been set."""
        doc = nlp.tokenizer(
            "family history of breast cancer but no diabetes. She has afib."
        )
        rule = ConTextRule("family history of", "FAMILY_HISTORY", direction="FORWARD")
        with pytest.raises(ValueError) as exception_info:
            # This should fail because doc.sents are None
            ConTextModifier(rule, 0, 3, doc)
        exception_info.match(
            # "ConText failed because sentence boundaries have not been set"
            "Sentence boundaries unset."
        )

    def test_set_scope_context_window_no_sentences(self):
        """Test that setting the scope succeeds if sentence boundaries haven't been set but _use_context_window is True."""
        doc = nlp.tokenizer(
            "family history of breast cancer but no diabetes. She has afib."
        )
        rule = ConTextRule(
            "family history of", "FAMILY_HISTORY", direction="FORWARD", max_scope=2
        )
        modifier = ConTextModifier(rule, 0, 3, doc, use_context_window=True)
        scope = modifier.scope_span
        assert doc[scope[0] : scope[1]] == doc[3:5]

    def test_update_scope(self):
        doc, rule, modifier = self.create_objects()
        modifier.update_scope(doc[3:5])

    def test_modifies(self):
        """Test that the ConTextModifier modifies a target in its scope"""
        doc, rule, modifier = self.create_objects()
        assert modifier.modifies(doc[3:5])

    def test_not_modifies(self):
        """Test that the ConTextModifier does not modify a target outside of its scope"""
        doc, rule, modifier = self.create_objects()
        assert not modifier.modifies(doc[-2:])

    def test_context_rule(self):
        doc, rule, modifier = self.create_objects()
        assert modifier.rule is rule

    def test_allowed_types(self):
        """Test that specifying allowed_types will only modify that target type."""
        doc = self.create_target_type_examples()
        rule = ConTextRule(
            "no history of travel to",
            category="DEFINITE_NEGATED_EXISTENCE",
            direction="FORWARD",
            allowed_types={"TRAVEL"},
        )
        modifier = ConTextModifier(rule, 0, 5, doc)
        travel, condition = doc.ents  # "puerto rico", "pneumonia"
        assert modifier.modifies(travel) is True
        assert modifier.modifies(condition) is False

    def test_excluded_types(self):
        """Test that specifying excluded_types will not modify that target type."""
        doc = self.create_target_type_examples()
        rule = ConTextRule(
            "no history of travel to",
            category="DEFINITE_NEGATED_EXISTENCE",
            direction="FORWARD",
            excluded_types={"CONDITION"},
        )
        modifier = ConTextModifier(rule, 0, 5, doc)
        travel, condition = doc.ents  # "puerto rico", "pneumonia"
        assert modifier.modifies(travel) is True
        assert modifier.modifies(condition) is False

    def test_no_types(self):
        """Test that not specifying allowed_types or excluded_types will modify all targets."""
        doc = self.create_target_type_examples()
        rule = ConTextRule(
            "no history of travel to",
            category="DEFINITE_NEGATED_EXISTENCE",
            direction="FORWARD",
        )
        modifier = ConTextModifier(rule, 0, 5, doc)
        travel, condition = doc.ents  # "puerto rico", "pneumonia"
        assert modifier.modifies(travel) is True
        assert modifier.modifies(condition) is True

    def test_max_targets_less_than_targets(self):
        """Check that if max_targets is not None it will reduce the targets
        to the two closest ents.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        rule = ConTextRule(
            "vs", category="UNCERTAIN", direction="BIDIRECTIONAL", max_targets=2
        )
        # Set "vs" to be the modifier
        modifier = ConTextModifier(rule, 5, 6, doc)
        for target in doc.ents:
            modifier.modify(target)
        assert modifier.num_targets == 3

        modifier.reduce_targets()
        assert modifier.num_targets == 2
        for target in modifier._targets:
            assert target.text.lower() in ("pneumonia", "copd")

    def test_max_targets_equal_to_targets(self):
        """Check that if max_targets is not None it will reduce the targets
        to the two closest ents.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        rule = ConTextRule(
            "vs", category="UNCERTAIN", direction="BIDIRECTIONAL", max_targets=3
        )
        # Set "vs" to be the modifier
        modifier = ConTextModifier(rule, 5, 6, doc)
        for target in doc.ents:
            modifier.modify(target)
        assert modifier.num_targets == 3

        modifier.reduce_targets()
        assert modifier.num_targets == 3

    def test_max_targets_none(self):
        """Check that if max_targets is None it will not reduce the targets
        to the two closest ents.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        rule = ConTextRule(
            "vs", category="UNCERTAIN", direction="BIDIRECTIONAL", max_targets=None
        )
        # Set "vs" to be the modifier
        modifier = ConTextModifier(rule, 5, 6, doc)
        for target in doc.ents:
            modifier.modify(target)
        assert modifier.num_targets == 3

        modifier.reduce_targets()
        assert modifier.num_targets == 3

    def test_max_scope(self):
        """Test that if max_scope is not None it will reduce the range
        of text which is modified.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        rule = ConTextRule(
            "vs", category="UNCERTAIN", direction="BIDIRECTIONAL", max_scope=1
        )
        modifier = ConTextModifier(rule, 5, 6, doc)

        for target in doc.ents:
            if modifier.modifies(target):
                modifier.modify(target)
        assert modifier.num_targets == 2
        for target in modifier._targets:
            assert target.text.lower() in ("pneumonia", "copd")

    def test_max_scope_none(self):
        """Test that if max_scope is not None it will reduce the range
        of text which is modified.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        rule = ConTextRule(
            "vs", category="UNCERTAIN", direction="BIDIRECTIONAL", max_scope=None
        )
        modifier = ConTextModifier(rule, 5, 6, doc)

        for target in doc.ents:
            if modifier.modifies(target):
                modifier.modify(target)
        assert modifier.num_targets == 3

    def test_overlapping_target(self):
        """Test that a modifier will not modify a target if it is
        in the same span as the modifier.
        """
        doc = nlp("Pt presents for r/o of pneumonia.")
        rule = ConTextRule("r/o", "UNCERTAIN", direction="BIDIRECTIONAL")
        modifier = ConTextModifier(rule, 3, 4, doc)
        target = Span(doc, 3, 4, "TEST")

        assert modifier.modifies(target) is False

    def test_on_modifies_true(self):
        def on_modifies(target, modifier, span_between):
            return True

        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", on_modifies=on_modifies
        )
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (Span(doc, 5, 6, "CONDITION"), Span(doc, 6, 8, "CONDITION"))
        mod = ConTextModifier(rule, 2, 5, doc)

        assert mod.modifies(doc.ents[0]) is True

    def test_on_modifies_false(self):
        def on_modifies(target, modifier, span_between):
            return False

        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", on_modifies=on_modifies
        )
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (Span(doc, 5, 6, "CONDITION"), Span(doc, 7, 8, "CONDITION"))
        modifier = ConTextModifier(rule, 2, 5, doc)

        assert modifier.modifies(doc.ents[0]) is False

    def test_on_modifies_custom_callback(self):
        def check_none_vals(target, _modifier, span_between):
            for arg in (target, _modifier, span_between):
                if arg is None:
                    return False
            return True

        rule = ConTextRule(
            "no evidence of", "NEGATED_EXISTENCE", on_modifies=check_none_vals
        )
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (Span(doc, 5, 6, "CONDITION"), Span(doc, 7, 8, "CONDITION"))
        modifier = ConTextModifier(rule, 2, 5, doc)

        assert modifier.modifies(doc.ents[0]) is True
