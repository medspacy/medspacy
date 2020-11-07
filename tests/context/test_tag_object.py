import pytest
import spacy
from spacy.tokens import Span, Doc

from medspacy.context import ConTextItem, ConTextComponent
from medspacy.context.tag_object import TagObject

nlp = spacy.load("en_core_web_sm")


class TestTagObject:
    def create_objects(self):
        doc = nlp("family history of breast cancer but no diabetes. She has afib.")
        item = ConTextItem("family history of", "FAMILY_HISTORY", rule="FORWARD")
        tag_object = TagObject(item, 0, 3, doc)
        return doc, item, tag_object

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
        doc, item, tag_object = self.create_objects()
        assert tag_object.span == doc[0:3]

    def test_set_span_fails(self):
        doc, item, tag_object = self.create_objects()
        with pytest.raises(AttributeError):
            tag_object.span = "Can't do this!"

    def test_rule(self):
        doc, item, tag_object = self.create_objects()
        assert tag_object.rule == "FORWARD"

    def test_category(self):
        doc, item, tag_object = self.create_objects()
        assert tag_object.category == "FAMILY_HISTORY"

    def test_default_scope(self):
        """Test that the scope goes from the end of the modifier phrase
        to the end of the sentence.
        """
        doc, item, tag_object = self.create_objects()
        assert tag_object.scope == doc[3:-4]

    def test_limit_scope(self):
        """Test that a 'TERMINATE' TagObject limits the scope of the tag object"""
        doc, item, tag_object = self.create_objects()
        item2 = ConTextItem("but", "TERMINATE", "TERMINATE")
        tag_object2 = TagObject(item2, 2, 4, doc)
        assert tag_object.limit_scope(tag_object2)

    def test_limit_scope2(self):
        doc, item, tag_object = self.create_objects()
        item2 = ConTextItem("but", "TERMINATE", "TERMINATE")
        tag_object2 = TagObject(item2, 2, 4, doc)
        assert not tag_object2.limit_scope(tag_object)

    def test_limit_scope3(self):
        """Test that two modifiers of the same type limit the scope of the first modifier."""
        doc = nlp("no evidence of CHF, neg for pneumonia")
        item = ConTextItem("no evidence of", "DEFINITE_NEGATED_EXISTENCE", "FORWARD")
        item2 = ConTextItem("neg for", "DEFINITE_NEGATED_EXISTENCE", "FORWARD")
        tag_object = TagObject(item, 0, 3, doc)
        tag_object2 = TagObject(item2, 5, 7, doc)
        assert tag_object.limit_scope(tag_object2)

    def test_terminate_limit_scope_custom(self):
        """Test that a modifier will be explicitly terminated by a modifier with a category
        in terminated_by."""
        doc = nlp("negative for flu, positive for pneumonia.")
        item = ConTextItem("negative for", "NEGATED_EXISTENCE", rule="FORWARD", terminated_by={"POSITIVE_EXISTENCE"})
        item2 = ConTextItem("positive for", "POSITIVE_EXISTENCE", rule="FORWARD")
        tag_object = TagObject(item, 0, 2, doc)
        tag_object2 = TagObject(item2, 4, 6, doc)
        assert tag_object.limit_scope(tag_object2)

    def test_terminate_limit_scope_custom2(self):
        """Test that a modifier will be explicitly terminated by a modifier with a category
        in terminated_by."""
        doc = nlp("flu is negative, pneumonia is positive.")
        item = ConTextItem("negative", "NEGATED_EXISTENCE", rule="BACKWARD")
        item2 = ConTextItem("positive", "POSITIVE_EXISTENCE", rule="BACKWARD", terminated_by={"NEGATED_EXISTENCE"})
        tag_object = TagObject(item, 2, 3, doc)
        tag_object2 = TagObject(item2, 6, 7, doc)
        assert tag_object2.limit_scope(tag_object)

    def test_terminate_limit_scope_backward(self):
        """Test that a 'TERMINATE' modifier will limit the scope of a 'BACKWARD' modifier.
        """
        doc = nlp("Pt has chf but pneumonia is ruled out")
        item = ConTextItem("is ruled out", "NEGATED_EXISTENCE", "BACKWARD")
        tag_object = TagObject(item, 6, 8, doc)

        item2 = ConTextItem("but", "TERMINATE", "TERMINATE")
        tag_object2 = TagObject(item2, 3, 4, doc)
        assert tag_object.limit_scope(tag_object2)

    def test_terminate_stops_forward_modifier(self):
        context = ConTextComponent(nlp, rules=None)

        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", "FORWARD")
        item2 = ConTextItem("but", "TERMINATE", "TERMINATE")
        context.add([item, item2])
        doc = nlp("No evidence of chf but she has pneumonia.")
        doc.ents = (Span(doc, 3, 4, "PROBLEM"), Span(doc, 7, 8, "PROBLEM"))
        context(doc)
        chf, pneumonia = doc.ents
        assert len(chf._.modifiers) > 0
        assert len(pneumonia._.modifiers) == 0

    def test_terminate_stops_backward_modifier(self):
        context = ConTextComponent(nlp, rules=None)

        item = ConTextItem("is ruled out", "NEGATED_EXISTENCE", "BACKWARD")
        item2 = ConTextItem("but", "CONJ", "TERMINATE")
        context.add([item, item2])
        doc = nlp("Pt has chf but pneumonia is ruled out")
        doc.ents = (Span(doc, 2, 3, "PROBLEM"), Span(doc, 4, 5, "PROBLEM"))
        context(doc)
        chf, pneumonia = doc.ents
        assert len(chf._.modifiers) == 0
        assert len(pneumonia._.modifiers) > 0

    def test_no_custom_terminate_stops_forward_modifier(self):
        doc = nlp("negative for flu, positive for pneumonia.")
        context = ConTextComponent(nlp, rules=None)

        item = ConTextItem("negative for", "NEGATED_EXISTENCE", rule="FORWARD", terminated_by=None)
        item2 = ConTextItem("positive for", "POSITIVE_EXISTENCE", rule="FORWARD")
        context.add([item, item2])
        doc.ents = (Span(doc, 2, 3, "PROBLEM"), Span(doc, 6, 7))
        flu, pneumonia = doc.ents
        context(doc)
        assert len(flu._.modifiers) == 1
        assert len(pneumonia._.modifiers) == 2

    def test_custom_terminate_stops_forward_modifier(self):
        doc = nlp("negative for flu, positive for pneumonia.")
        context = ConTextComponent(nlp, rules=None)

        item = ConTextItem("negative for", "NEGATED_EXISTENCE", rule="FORWARD", terminated_by={"POSITIVE_EXISTENCE"})
        item2 = ConTextItem("positive for", "POSITIVE_EXISTENCE", rule="FORWARD")
        context.add([item, item2])
        doc.ents = (Span(doc, 2, 3, "PROBLEM"), Span(doc, 6, 7))
        flu, pneumonia = doc.ents
        context(doc)
        assert len(flu._.modifiers) == 1
        assert len(pneumonia._.modifiers) == 1


    def test_no_limit_scope_same_category_different_allowed_types(self):
        """Test that a two TagObjects of the same type but with different
         allowed types does not limits the scope of the tag object.
         """
        doc = nlp("no history of travel to Puerto Rico, neg for pneumonia")

        item = ConTextItem(
            "no history of",
            "DEFINITE_NEGATED_EXISTENCE",
            "FORWARD",
            allowed_types={"TRAVEL"},
        )
        item2 = ConTextItem(
            "neg for",
            "DEFINITE_NEGATED_EXISTENCE",
            "FORWARD",
            allowed_types={"CONDITION"},
        )
        tag_object = TagObject(item, 0, 3, doc)
        tag_object2 = TagObject(item2, 8, 10, doc)
        assert not tag_object.limit_scope(tag_object2)

    def test_set_scope_fails_no_sentences(self):
        """Test that setting the scope fails if sentence boundaries haven't been set."""
        doc = nlp.tokenizer("family history of breast cancer but no diabetes. She has afib.")
        item = ConTextItem("family history of", "FAMILY_HISTORY", rule="FORWARD")
        with pytest.raises(ValueError) as exception_info:
            # This should fail because doc.sents are None
            TagObject(item, 0, 3, doc)
        exception_info.match(
            "ConText failed because sentence boundaries have not been set"
        )

    def test_set_scope_context_window_no_sentences(self):
        """Test that setting the scope succeeds if sentence boundaries haven't been set but _use_context_window is True."""
        doc = nlp.tokenizer("family history of breast cancer but no diabetes. She has afib.")
        item = ConTextItem("family history of", "FAMILY_HISTORY", rule="FORWARD", max_scope=2)
        tag_object = TagObject(item, 0, 3, doc, _use_context_window=True)
        assert tag_object.scope == doc[3:5]

    def test_update_scope(self):
        doc, item, tag_object = self.create_objects()
        tag_object.update_scope(doc[3:5])

    def test_modifies(self):
        """Test that the TagObject modifies a target in its scope"""
        doc, item, tag_object = self.create_objects()
        assert tag_object.modifies(doc[3:5])

    def test_not_modifies(self):
        """Test that the TagObject does not modify a target outside of its scope"""
        doc, item, tag_object = self.create_objects()
        assert not tag_object.modifies(doc[-2:])

    def test_context_item(self):
        doc, item, tag_object = self.create_objects()
        assert tag_object.context_item is item

    def test_allowed_types(self):
        """Test that specifying allowed_types will only modify that target type."""
        doc = self.create_target_type_examples()
        item = ConTextItem(
            "no history of travel to",
            category="DEFINITE_NEGATED_EXISTENCE",
            rule="FORWARD",
            allowed_types={"TRAVEL"},
        )
        tag_object = TagObject(item, 0, 5, doc)
        tag_object.set_scope()
        travel, condition = doc.ents  # "puerto rico", "pneumonia"
        assert tag_object.modifies(travel) is True
        assert tag_object.modifies(condition) is False

    def test_excluded_types(self):
        """Test that specifying excluded_types will not modify that target type."""
        doc = self.create_target_type_examples()
        item = ConTextItem(
            "no history of travel to",
            category="DEFINITE_NEGATED_EXISTENCE",
            rule="FORWARD",
            excluded_types={"CONDITION"},
        )
        tag_object = TagObject(item, 0, 5, doc)
        tag_object.set_scope()
        travel, condition = doc.ents  # "puerto rico", "pneumonia"
        assert tag_object.modifies(travel) is True
        assert tag_object.modifies(condition) is False

    def test_no_types(self):
        """Test that not specifying allowed_types or excluded_types will modify all targets."""
        doc = self.create_target_type_examples()
        item = ConTextItem(
            "no history of travel to",
            category="DEFINITE_NEGATED_EXISTENCE",
            rule="FORWARD",
        )
        tag_object = TagObject(item, 0, 5, doc)
        tag_object.set_scope()
        travel, condition = doc.ents  # "puerto rico", "pneumonia"
        assert tag_object.modifies(travel) is True
        assert tag_object.modifies(condition) is True

    def test_max_targets_less_than_targets(self):
        """Check that if max_targets is not None it will reduce the targets
        to the two closest ents.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        item = ConTextItem(
            "vs", category="UNCERTAIN", rule="BIDIRECTIONAL", max_targets=2
        )
        # Set "vs" to be the modifier
        tag_object = TagObject(item, 5, 6, doc)
        for target in doc.ents:
            tag_object.modify(target)
        assert tag_object.num_targets == 3

        tag_object.reduce_targets()
        assert tag_object.num_targets == 2
        for target in tag_object._targets:
            assert target.lower_ in ("pneumonia", "copd")

    def test_max_targets_equal_to_targets(self):
        """Check that if max_targets is not None it will reduce the targets
        to the two closest ents.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        item = ConTextItem(
            "vs", category="UNCERTAIN", rule="BIDIRECTIONAL", max_targets=3
        )
        # Set "vs" to be the modifier
        tag_object = TagObject(item, 5, 6, doc)
        for target in doc.ents:
            tag_object.modify(target)
        assert tag_object.num_targets == 3

        tag_object.reduce_targets()
        assert tag_object.num_targets == 3

    def test_max_targets_none(self):
        """Check that if max_targets is None it will not reduce the targets
        to the two closest ents.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        item = ConTextItem(
            "vs", category="UNCERTAIN", rule="BIDIRECTIONAL", max_targets=None
        )
        # Set "vs" to be the modifier
        tag_object = TagObject(item, 5, 6, doc)
        for target in doc.ents:
            tag_object.modify(target)
        assert tag_object.num_targets == 3

        tag_object.reduce_targets()
        assert tag_object.num_targets == 3

    def test_max_scope(self):
        """Test that if max_scope is not None it will reduce the range
        of text which is modified.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        item = ConTextItem(
            "vs", category="UNCERTAIN", rule="BIDIRECTIONAL", max_scope=1
        )
        tag_object = TagObject(item, 5, 6, doc)

        for target in doc.ents:
            if tag_object.modifies(target):
                tag_object.modify(target)
        assert tag_object.num_targets == 2
        for target in tag_object._targets:
            assert target.lower_ in ("pneumonia", "copd")

    def test_max_scope_none(self):
        """Test that if max_scope is not None it will reduce the range
        of text which is modified.
        """
        doc = self.create_num_target_examples()
        assert len(doc.ents) == 3
        item = ConTextItem(
            "vs", category="UNCERTAIN", rule="BIDIRECTIONAL", max_scope=None
        )
        tag_object = TagObject(item, 5, 6, doc)

        for target in doc.ents:
            if tag_object.modifies(target):
                tag_object.modify(target)
        assert tag_object.num_targets == 3



    def test_overlapping_target(self):
        """Test that a modifier will not modify a target if it is
        in the same span as the modifier.
        """
        doc = nlp("Pt presents for r/o of pneumonia.")
        item = ConTextItem("r/o", "UNCERTAIN", rule="BIDIRECTIONAL")
        tag_object = TagObject(item, 3, 4, doc)
        target = Span(doc, 3, 4, "TEST")

        assert tag_object.modifies(target) is False

    def test_on_modifies_true(self):
        def on_modifies(target, modifier, span_between):
            return True

        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", on_modifies=on_modifies)
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (doc[5:6], doc[7:8])
        tag = TagObject(item, 2, 5, doc)

        assert tag.modifies(doc.ents[0]) is True

    def test_on_modifies_false(self):
        def on_modifies(target, modifier, span_between):
            return False

        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", on_modifies=on_modifies)
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (doc[5:6], doc[7:8])
        tag = TagObject(item, 2, 5, doc)

        assert tag.modifies(doc.ents[0]) is False


    def test_on_modifies_arg_types(self):
        def check_arg_types(target, modifier, span_between):
            for arg in (target, modifier, span_between):
                if not isinstance(arg, spacy.tokens.Span):
                    return False
            return True

        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", on_modifies=check_arg_types)
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (doc[5:6], doc[7:8])
        tag = TagObject(item, 2, 5, doc)

        assert tag.modifies(doc.ents[0]) is True

    def test_on_modifies_arg_values(self):
        def check_arg_types(target, modifier, span_between):
            if target.lower_ != "chf":
                return False
            if modifier.lower_ != "no evidence of":
                return False
            if span_between.lower_ != "pneumonia or":
                return False
            return True

        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", on_modifies=check_arg_types)
        doc = nlp("There is no evidence of pneumonia or chf.")
        doc.ents = (doc[5:6], doc[7:8])
        tag = TagObject(item, 2, 5, doc)

        assert tag.modifies(doc.ents[1]) is True
