import spacy
from spacy.pipeline import EntityRuler

from medspacy.io import DocConsumer
from medspacy.context import ConTextComponent
from medspacy.section_detection import Sectionizer, SectionRule

nlp = spacy.load("en_core_web_sm")
nlp.remove_pipe("ner")

matcher = EntityRuler(nlp)
matcher.add_patterns([{"label": "PROBLEM", "pattern": "cough"}])
nlp.add_pipe(matcher)

context = ConTextComponent(nlp)
nlp.add_pipe(context)

sectionizer = Sectionizer(nlp)
sectionizer.add(
    [
        SectionRule("Section 1:", "section1"),
        SectionRule("Section 2:", "section2", parents=["section1"]),
    ]
)
nlp.add_pipe(sectionizer)

simple_text = "Patient has a cough."
context_text = "Patient has no cough."
section_text = "Section 1: Patient has a cough"
section_parent_text = """Section 1: comment
Section 2: Patient has a cough"""
many_concept_texts = ["cough " * i for i in range(10)]

simple_doc = nlp(simple_text)
context_doc = nlp(context_text)
section_doc = nlp(section_text)
section_parent_doc = nlp(section_parent_text)
many_concept_docs = [nlp(t) for t in many_concept_texts]


class TestDocConsumer:
    def test_init_default(self):
        assert DocConsumer(nlp)

    def test_init_context(self):
        assert DocConsumer(nlp, context=True)

    def test_init_sections(self):
        assert DocConsumer(nlp, sectionizer=True)

    def test_init_all(self):
        assert DocConsumer(nlp, context=True, sectionizer=True)

    def test_default_cols(self):
        consumer = DocConsumer(nlp)
        doc = consumer(simple_doc)
        data = doc._.get_data("ent")
        assert data is not None
        assert set(data.keys()) == set(consumer.attrs)

    def test_context_cols(self):
        consumer = DocConsumer(nlp, context=True)
        doc = consumer(context_doc)
        data = doc._.get_data("ent")
        assert data is not None
        assert set(data.keys()) == set(consumer.attrs)

    def test_section_cols_ent(self):
        consumer = DocConsumer(nlp, sectionizer=True)
        doc = consumer(context_doc)
        data = doc._.get_data("ent")
        assert data is not None
        assert set(data.keys()) == set(consumer.attrs)

    def test_section_cols_section(self):
        consumer = DocConsumer(nlp, sectionizer=True)
        doc = consumer(context_doc)
        data = doc._.get_data("section")
        assert data is not None
        assert set(data.keys()) == set(consumer.section_attrs)

    def test_all_cols(self):
        consumer = DocConsumer(nlp, sectionizer=True, context=True)
        doc = consumer(context_doc)
        data = doc._.get_data("ent")
        assert data is not None
        assert set(data.keys()) == set(consumer.attrs)

    def test_default_data(self):
        consumer = DocConsumer(nlp)
        doc = consumer(simple_doc)
        data = doc._.get_data("ent")
        ent = doc.ents[0]
        assert data["text"][0] == ent.text
        assert data["label_"][0] == ent.label_
        assert data["start_char"][0] == ent.start_char
        assert data["end_char"][0] == ent.end_char

    def test_context_data(self):
        consumer = DocConsumer(nlp, context=True)
        doc = consumer(context_doc)
        data = doc._.get_data("ent")
        ent = doc.ents[0]
        assert data["is_family"][0] == ent._.is_family
        assert data["is_hypothetical"][0] == ent._.is_hypothetical
        assert data["is_historical"][0] == ent._.is_historical
        assert data["is_uncertain"][0] == ent._.is_uncertain
        assert data["is_negated"][0] == ent._.is_negated

    def test_section_data_ent(self):
        consumer = DocConsumer(nlp, sectionizer=True)
        doc = consumer(section_doc)
        data = doc._.get_data("ent")
        ent = doc.ents[0]
        assert data["section_title"][0] == ent._.section_title
        assert data["section_parent"][0] == ent._.section_parent

    def test_section_data_ent_parent(self):
        consumer = DocConsumer(nlp, sectionizer=True)
        doc = consumer(section_parent_doc)
        data = doc._.get_data("ent")
        ent = doc.ents[0]
        assert data["section_title"][0] == ent._.section_title
        assert data["section_parent"][0] == ent._.section_parent

    def test_section_data_section(self):
        consumer = DocConsumer(nlp, sectionizer=True)
        doc = consumer(section_doc)
        data = doc._.get_data("section")
        section = doc._.sections[0]
        assert data["section_category"][0] == section.category
        assert data["section_title_text"][0] == section.title_span.text
        assert data["section_title_start_char"][0] == section.title_span.start_char
        assert data["section_title_end_char"][0] == section.title_span.end_char
        assert data["section_text"][0] == section.section_span.text
        assert data["section_text_start_char"][0] == section.section_span.start_char
        assert data["section_text_end_char"][0] == section.section_span.end_char
        assert data["section_parent"][0] == section.parent

    def test_ten_concepts(self):
        consumer = DocConsumer(nlp)
        docs = [consumer(d) for d in many_concept_docs]
        for doc in docs:
            print(doc)
            num_concepts = len(doc.ents)
            data = doc._.get_data("ent")
            for key in data.keys():
                print(key)
                print(num_concepts)
                print(data[key])
                assert num_concepts == len(data[key])
