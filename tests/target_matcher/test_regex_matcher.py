import spacy
import warnings

from medspacy.target_matcher.regex_matcher import RegexMatcher

nlp = spacy.load("en_core_web_sm")


class TestTargetMatcher:
    def test_initiate(self):
        assert RegexMatcher(nlp.vocab)


    def test_add(self):
        matcher = RegexMatcher(nlp.vocab)
        matcher.add(
            "my_rule",
            ["my_pattern"]
        )
        assert matcher._patterns

    def test_basic_match(self):
        matcher = RegexMatcher(nlp.vocab)
        matcher.add(
            "CONDITION",
            ["pulmonary embolisms?"]
        )
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
        matcher.add(
            "ENTITY",
            ['ICE: Rad']
        )
        doc = nlp('SERVICE: Radiology')
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == 'SERVICE: Radiology'

    def test_resolve_start_right(self):
        matcher = RegexMatcher(nlp.vocab, resolve_start="right")
        matcher.add(
            "ENTITY",
            ['ICE: Rad']
        )
        doc = nlp('SERVICE: Radiology')
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == ': Radiology'

    def test_resolve_end_left(self):
        matcher = RegexMatcher(nlp.vocab, resolve_end="left")
        matcher.add(
            "ENTITY",
            ['ICE: Rad']
        )
        doc = nlp('SERVICE: Radiology')
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == 'SERVICE:'

    def test_resolve_inward(self):
        matcher = RegexMatcher(nlp.vocab, resolve_start="right", resolve_end="left")
        matcher.add(
            "ENTITY",
            ['ICE: Rad']
        )
        doc = nlp('SERVICE: Radiology')
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == ':'

    def test_resolve_single_matched_token(self):
        matcher = RegexMatcher(nlp.vocab, resolve_start="left", resolve_end="right")
        matcher.add(
            "ENTITY",
            ['ICE']
        )
        doc = nlp('SERVICE: Radiology')
        matches = matcher(doc)
        assert matches
        _, start, end = matches[0]
        span = doc[start:end]
        assert span.text == 'SERVICE'

    def test_resolve_inward_single_matched_token_is_none(self):
        matcher = RegexMatcher(nlp.vocab, resolve_start="right", resolve_end="left")
        matcher.add(
            "ENTITY",
            ['ICE']
        )
        doc = nlp('SERVICE: Radiology')
        matches = matcher(doc)
        assert matches == []

    #
    # def test_add_ents_false(self):
    #     matcher = TargetMatcher(nlp, add_ents=False)
    #     matcher.add(
    #         [TargetRule("PE", "CONDITION")]
    #     )
    #     doc = nlp("Past Medical History: PE")
    #     spans = matcher(doc)
    #
    #     assert len(doc.ents) == 0
    #
    #     assert len(spans) == 1
    #     assert isinstance(spans[0], spacy.tokens.Span)
    #
    # def test_add_rule_pattern(self):
    #     matcher = TargetMatcher(nlp)
    #     matcher.add(
    #         [TargetRule("PE", "CONDITION", pattern=[{"LOWER": "pe"}])]
    #     )
    #     doc = nlp("Past Medical History: Pe")
    #     matcher(doc)
    #     assert len(doc.ents) == 1
    #     assert (doc.ents[0].start, doc.ents[0].end) == (4, 5)
    #     assert doc.ents[0].label_ == "CONDITION"
    #
    # def test_add_rule_regex(self):
    #     matcher = TargetMatcher(nlp)
    #     matcher.add(
    #         [TargetRule("PE", "CONDITION", pattern="pulmonary embolisms?")]
    #     )
    #     doc = nlp("Past Medical History: Pulmonary embolism")
    #     matcher(doc)
    #     assert len(doc.ents) == 1
    #     assert (doc.ents[0].start, doc.ents[0].end) == (4, 6)
    #     assert doc.ents[0].label_ == "CONDITION"
