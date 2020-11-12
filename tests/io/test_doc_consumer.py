import spacy
from spacy.pipeline import EntityRuler

from medspacy.io import DocConsumer
from medspacy.context import ConTextComponent
from medspacy.section_detection import Sectionizer

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
        {"section_title": "section1", "pattern": "Section 1:"},
        {"section_title": "section2", "pattern": "Section 2:", "parents": ["section1"]},
    ]
)
nlp.add_pipe(sectionizer)

simple_text = "Patient has a cough."
context_text = "Patient has no cough."
section_text = """Section 1: comment
Section 2: Patient has a cough"""

simple_doc = nlp(simple_text)
context_doc = nlp(context_text)
section_doc = nlp(section_text)


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
        assert data["text"] == ["cough"]
        assert data["label_"] == ["PROBLEM"]
        assert data["start_char"] == [14]
        assert data["end_char"] == [19]

    def test_context_data(self):
        consumer = DocConsumer(nlp, context=True)
        doc = consumer(context_doc)
        data = doc._.get_data("ent")
        assert data["is_family"] == [False]
        assert data["is_hypothetical"] == [False]
        assert data["is_historical"] == [False]
        assert data["is_uncertain"] == [False]
        assert data["is_negated"] == [True]

    # this is failing for some reason
    def test_section_data_ent(self):
        consumer = DocConsumer(nlp, sectionizer=True)
        doc = consumer(section_doc)
        data = doc._.get_data("ent")
        print(type(data["section_parent"][0]))
        assert data["section_title"] == ["section2"]
        assert data["section_parent"] == ["section1"]
