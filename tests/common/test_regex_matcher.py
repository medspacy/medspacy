import spacy
import warnings

from medspacy.common.regex_matcher import RegexMatcher

nlp = spacy.blank("en")


class TestTargetMatcher:
    def test_initiate(self):
        assert RegexMatcher(nlp.vocab)

    def test_add(self):
        matcher = RegexMatcher(nlp.vocab)
        matcher.add("my_rule", ["my_pattern"])
        assert matcher._patterns

    def test_basic_match(self):
        matcher = RegexMatcher(nlp.vocab)
        matcher.add("CONDITION", ["pulmonary embolisms?"])
        doc = nlp("Past Medical History: Pulmonary embolism")
        matches = matcher(doc)
        assert matches
        match_id, start, end = matches[0]
        assert start, end == (4, 5)
        assert nlp.vocab[match_id] == "CONDITION"
        span = doc[start:end]
        assert span.text == "Pulmonary embolism"

    def test_resolve_default(self):
        matcher = RegexMatcher(nlp.vocab)
        matcher.add("ENTITY", ["ICE: Rad"])
        doc = nlp("SERVICE: Radiology")
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == "SERVICE: Radiology"

    def test_resolve_start_right(self):
        matcher = RegexMatcher(nlp.vocab, resolve_start="right")
        matcher.add("ENTITY", ["ICE: Rad"])
        doc = nlp("SERVICE: Radiology")
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == ": Radiology"

    def test_resolve_end_left(self):
        matcher = RegexMatcher(nlp.vocab, resolve_end="left")
        matcher.add("ENTITY", ["ICE: Rad"])
        doc = nlp("SERVICE: Radiology")
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == "SERVICE:"

    def test_resolve_inward(self):
        matcher = RegexMatcher(nlp.vocab, resolve_start="right", resolve_end="left")
        matcher.add("ENTITY", ["ICE: Rad"])
        doc = nlp("SERVICE: Radiology")
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == ":"

    def test_resolve_single_matched_token(self):
        matcher = RegexMatcher(nlp.vocab, resolve_start="left", resolve_end="right")
        matcher.add("ENTITY", ["ICE"])
        doc = nlp("SERVICE: Radiology")
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == "SERVICE"

    def test_resolve_inward_single_matched_token_is_none(self):
        matcher = RegexMatcher(nlp.vocab, resolve_start="right", resolve_end="left")
        matcher.add("ENTITY", ["ICE"])
        doc = nlp("SERVICE: Radiology")
        matches = matcher(doc)
        assert matches == []
