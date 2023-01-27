import spacy
from medspacy.postprocess import PostprocessingPattern


import tempfile

tmpdirname = tempfile.TemporaryDirectory()

nlp = spacy.blank("en")

class TestMedSpaCyExtensions:
    def test_postprocess_pattern(self):
        # Test with a default value of True
        pattern = PostprocessingPattern(lambda x: True)
        doc = nlp("This is a doc.")
        ent = doc[:1]
        rslt = pattern(ent)
        assert rslt is True

    def test_postprocess_pattern_success_false(self):
        # Test with a default value of True
        pattern = PostprocessingPattern(lambda x: False)
        doc = nlp("This is a doc.")
        ent = doc[:1]
        rslt = pattern(ent)
        assert rslt is False

    def test_postprocess_pattern_false(self):
        # Test with a default value of True
        pattern = PostprocessingPattern(lambda x: False, success_value=False)
        doc = nlp("This is a doc.")
        ent = doc[:1]
        rslt = pattern(ent)
        assert rslt is True

