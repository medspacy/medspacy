import spacy
from spacy.tokens import Token
from medspacy.target_matcher import ConceptTagger


import tempfile

tmpdirname = tempfile.TemporaryDirectory()



class TestMedSpaCyExtensions:

    def test_concept_tagger_set_concept_tag_attr(self):
        nlp = spacy.blank("en")
        assert Token.has_extension("concept_tag") is False
        concept_tagger = nlp.add_pipe("medspacy_concept_tagger")
        assert Token.has_extension("concept_tag") is True

    def test_concept_tagger_set_concept_tag_attr_twice(self):
        """Make sure that you can instantiate the ConceptTagger twice
        and spaCy doesn't throw an error about the attribute."""
        nlp = spacy.blank("en")
        concept_tagger = nlp.add_pipe("medspacy_concept_tagger")
        nlp.remove_pipe("medspacy_concept_tagger")
        nlp.add_pipe("medspacy_concept_tagger")

    def test_concept_tagger_set_custom_attr(self):
        nlp = spacy.blank("en")
        attr_name = "my_attre"
        assert Token.has_extension(attr_name) is False
        concept_tagger = nlp.add_pipe("medspacy_concept_tagger", config=dict(attr_name=attr_name))
        assert Token.has_extension(attr_name) is True

       