import spacy
import warnings

from medspacy.target_matcher import TargetMatcher, TargetRule

nlp = spacy.load("en_core_web_sm")


class TestTargetMatcher:
    def test_initiate(self):
        assert TargetMatcher(nlp)


    def test_add(self):
        matcher = TargetMatcher(nlp)
        matcher.add(
            [TargetRule("my direction", "RULE")]
        )
        assert matcher._rules

    def test_basic_rule(self):
        matcher = TargetMatcher(nlp)
        matcher.add(
            [TargetRule("PE", "CONDITION")]
        )
        doc = nlp("Past Medical History: PE")
        matcher(doc)
        assert len(doc.ents) == 1
        assert (doc.ents[0].start, doc.ents[0].end) == (4, 5)
        assert doc.ents[0].label_ == "CONDITION"

    def test_add_ents_false(self):
        matcher = TargetMatcher(nlp, add_ents=False)
        matcher.add(
            [TargetRule("PE", "CONDITION")]
        )
        doc = nlp("Past Medical History: PE")
        spans = matcher(doc)

        assert len(doc.ents) == 0

        assert len(spans) == 1
        assert isinstance(spans[0], spacy.tokens.Span)

    def test_add_rule_pattern(self):
        matcher = TargetMatcher(nlp)
        matcher.add(
            [TargetRule("PE", "CONDITION", pattern=[{"LOWER": "pe"}])]
        )
        doc = nlp("Past Medical History: Pe")
        matcher(doc)
        assert len(doc.ents) == 1
        assert (doc.ents[0].start, doc.ents[0].end) == (4, 5)
        assert doc.ents[0].label_ == "CONDITION"

    def test_add_rule_regex(self):
        matcher = TargetMatcher(nlp)
        matcher.add(
            [TargetRule("PE", "CONDITION", pattern="pulmonary embolisms?")]
        )
        doc = nlp("Past Medical History: Pulmonary embolism")
        matcher(doc)
        assert len(doc.ents) == 1
        assert (doc.ents[0].start, doc.ents[0].end) == (4, 6)
        assert doc.ents[0].label_ == "CONDITION"
