from typing import List
import pytest
import spacy
import srsly
from spacy.tokens import Span, Doc
from medspacy.context import ConTextRule, ConTextGraph, ConTextModifier
from medspacy.section_detection import Section, SectionRule, Sectionizer

Span.set_extension("modifiers", default=(), force=True)
Doc.set_extension("context_graph", default=None, force=True)


@pytest.fixture(scope="module")
def nlp():
    nlp = spacy.load("en_core_web_sm")
    return nlp


class TestSerialization:
    @pytest.fixture(scope="class")
    def doc_with_context(self, nlp) -> ConTextGraph:
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
        doc._.context_graph = graph
        return doc

    @pytest.fixture(scope="class")
    def doc_with_sections(self, nlp) -> Doc:
        sectionizer = Sectionizer(
            nlp, rules=None, span_attrs={"past_medical_history": {"is_negated": True}}
        )
        sectionizer.add([SectionRule("Past Medical History:", "past_medical_history")])
        doc = nlp("Past Medical History: Pneumonia")

        doc.ents = (Span(doc, 4, 5, "CONDITION"),)
        doc = sectionizer(doc)
        return doc

    def test_serialize_context_modifier(self, nlp):
        doc = nlp.tokenizer("There is no evidence of pneumonia but there is chf.")
        doc[0].is_sent_start = True
        for token in doc[1:]:
            token.is_sent_start = False
        item_data2 = ConTextRule("evidence of", "DEFINITE_EXISTENCE", "forward")
        tag_object2 = ConTextModifier(item_data2, 3, 5, doc)

        serialized = srsly.msgpack_dumps({"modifier": tag_object2})

        deserialized = srsly.msgpack_loads(serialized)

        assert isinstance(deserialized, ConTextModifier)

    def test_serialize_doc_with_sections(self, doc_with_sections):
        vocab = doc_with_sections.vocab
        serialized_doc = doc_with_sections.to_bytes()
        deserialized_doc = Doc(vocab).from_bytes(serialized_doc)

        assert len(deserialized_doc._.sections) > 0
        assert isinstance(deserialized_doc._.sections[0], Section)

    def test_serialize_doc_with_context(self, doc_with_context):
        vocab = doc_with_context.vocab
        serialized_doc = doc_with_context.to_bytes()
        deserialized_doc = Doc(vocab).from_bytes(serialized_doc)

        assert isinstance(deserialized_doc._.context_graph, ConTextGraph)
        assert len(deserialized_doc._.context_graph.modifiers) > 0
        assert isinstance(
            deserialized_doc._.context_graph.modifiers[0], ConTextModifier
        )
