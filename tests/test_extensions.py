import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
import pytest
import sys

import medspacy

import spacy

from medspacy._extensions import (
    _token_extensions,
    _span_extensions,
    _doc_extensions,
    _context_attributes,
)

nlp = spacy.blank("en")
doc = nlp("There is no evidence of pneumonia in the chest x-ray.")


class TestMedSpaCyExtensions:
    def test_token_attributes(self):
        for attr in _token_extensions.keys():
            assert hasattr(doc[0]._, attr)

    def test_span_attributes(self):
        for attr in _span_extensions.keys():
            assert hasattr(doc[0:1]._, attr)

    # @pytest.mark.skip(reason="Not sure why this is failing - manually checking this shows it works. "
    #              "Skipping for now.")
    def test_doc_attributes(self):
        for attr in _doc_extensions.keys():
            assert hasattr(doc._, attr)

    def test_token_window_default(self):
        token = doc[3]
        window = token._.window()
        assert window == doc[2:5]

    def test_token_window_custom(self):
        token = doc[3]
        window = token._.window(2)
        assert window == doc[1:6]

    def test_token_window_left_false(self):
        token = doc[3]
        window = token._.window(2, left=False)
        assert window == doc[3:6]

    def test_token_window_right_false(self):
        token = doc[3]
        window = token._.window(2, right=False)
        assert window == doc[1:4]

    def test_span_window_default(self):
        span = doc[3:5]
        window = span._.window()
        assert window == doc[2:6]

    def test_span_window_custom(self):
        span = doc[3:5]
        window = span._.window(2)
        assert window == doc[1:7]

    def test_span_window_left_false(self):
        span = doc[3:5]
        window = span._.window(2, left=False)
        assert window == doc[3:7]

    def test_span_window_right_false(self):
        span = doc[3:5]
        window = span._.window(2, right=False)
        assert window == doc[1:5]

    def test_span_context_attributes(self):
        span = doc[3:5]
        context_dict = span._.context_attributes
        assert set(context_dict.keys()) == {
            "is_negated",
            "is_hypothetical",
            "is_uncertain",
            "is_historical",
            "is_family",
        }
        assert set(context_dict.values()) == {False}

    def test_span_not_any_context_attributes(self):
        span = doc[3:5]
        assert span._.any_context_attributes is False

    def test_span_any_context_attributes(self):
        span = doc[3:5]
        span._.is_negated = True
        assert span._.any_context_attributes is True

    def test_span_contains(self):
        span = doc[3:6]
        assert span._.contains(r"of\s+pneumonia")

    def test_span_contains_regex_false(self):
        span = doc[3:6]
        assert not span._.contains(r"of\s+pneumonia", regex=False)

    def test_span_contains_list(self):
        span = doc[3:6]
        assert span._.contains(["pna", "pneumonia"])
