import pytest
import spacy

from medspacy.context import ConTextComponent
from medspacy.context import ConTextRule
from medspacy.context.context_modifier import ConTextModifier
from medspacy.context.context_graph import ConTextGraph
from spacy.tokens import Span
from medspacy.context.context_graph import overlap_target_modifiers

nlp = spacy.load("en_core_web_sm")


class TestConTextGraph:
    def context_graph(self):
        doc = nlp.tokenizer("There is no evidence of pneumonia but there is chf.")
        doc[0].is_sent_start = True
        for token in doc[1:]:
            token.is_sent_start = False
        item_data1 = ConTextRule(
            "no evidence of", "DEFINITE_NEGATED_EXISTENCE", "forward"
        )
        tag_object1 = ConTextModifier(item_data1, 2, 5, doc)

        item_data2 = ConTextRule("evidence of", "DEFINITE_EXISTENCE", "forward")
        tag_object2 = ConTextModifier(item_data2, 3, 5, doc)

        item_data3 = ConTextRule("but", "TERMINATE", "TERMINATE")
        tag_object3 = ConTextModifier(item_data3, 6, 7, doc)

        graph = ConTextGraph()
        graph.modifiers = [tag_object1, tag_object2, tag_object3]
        return doc, graph

    def test_init(self):
        assert ConTextGraph()

    def test_apply_modifiers(self):
        doc, graph = self.context_graph()
        graph.targets = [doc[5:6]]  # "pneumonia"
        graph.apply_modifiers()
        assert len(graph.edges) == 2

    def test_prune_modifiers(self):
        doc, graph = self.context_graph()
        graph.targets = [doc[5:6]]  # "pneumonia"
        graph.prune_modifiers()
        assert len(graph.modifiers) == 2

    def test_update_scopes(self):
        doc, graph = self.context_graph()
        graph.targets = [doc[5:6]]  # "pneumonia"
        graph.apply_modifiers()
        assert graph.modifiers[0].scope == doc[5:]
        graph.update_scopes()
        assert graph.modifiers[0].scope == doc[5:6]

    def test_remove_modifiers_overlap_target(self):
        """Test that a modifier which overlaps with a target is removed when set to True."""
        doc = nlp("The patient has heart failure.")
        doc.ents = (Span(doc, 3, 5, "CONDITION"),)
        context_item = ConTextRule("failure", "MODIFIER")
        tag_object = ConTextModifier(context_item, 4, 5, doc)
        graph = ConTextGraph(remove_overlapping_modifiers=True)

        graph.modifiers = [tag_object]
        graph.targets = doc.ents
        graph.prune_modifiers()
        graph.apply_modifiers()

        assert overlap_target_modifiers(tag_object.span, doc.ents[0])
        assert len(graph.modifiers) == 0

    def test_not_remove_modifiers_overlap_target(self):
        """Test that a modifier which overlaps with a target is not pruned but does not modify itself."""
        doc = nlp("The patient has heart failure.")
        doc.ents = (Span(doc, 3, 5, "CONDITION"),)
        context_item = ConTextRule("failure", "MODIFIER")
        tag_object = ConTextModifier(context_item, 4, 5, doc)
        graph = ConTextGraph(remove_overlapping_modifiers=False)

        graph.modifiers = [tag_object]
        graph.targets = doc.ents
        graph.prune_modifiers()
        graph.apply_modifiers()

        assert overlap_target_modifiers(tag_object.span, doc.ents[0])
        assert len(graph.modifiers) == 1


