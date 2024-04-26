import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
import spacy
import warnings

from medspacy.target_matcher import TargetMatcher, TargetRule

nlp = spacy.load("en_core_web_sm")


class TestTargetMatcher:
    def test_initiate(self):
        assert TargetMatcher(nlp)

    def test_add(self):
        matcher = TargetMatcher(nlp)
        matcher.add([TargetRule("my direction", "RULE")])
        assert matcher.rules

    def test_basic_rule(self):
        matcher = TargetMatcher(nlp)
        matcher.add([TargetRule("PE", "CONDITION")])
        doc = nlp("Past Medical History: PE")
        matcher(doc)
        assert len(doc.ents) == 1
        assert (doc.ents[0].start, doc.ents[0].end) == (4, 5)
        assert doc.ents[0].label_ == "CONDITION"

    def test_add_result_type_none(self):
        matcher = TargetMatcher(nlp, result_type=None)
        matcher.add([TargetRule("PE", "CONDITION")])
        doc = nlp("Past Medical History: PE")
        spans = matcher(doc)

        assert len(doc.ents) == 0

        assert len(spans) == 1
        assert isinstance(spans[0], spacy.tokens.Span)

    def test_add_rule_pattern(self):
        matcher = TargetMatcher(nlp)
        matcher.add([TargetRule("PE", "CONDITION", pattern=[{"LOWER": "pe"}])])
        doc = nlp("Past Medical History: Pe")
        matcher(doc)
        assert len(doc.ents) == 1
        assert (doc.ents[0].start, doc.ents[0].end) == (4, 5)
        assert doc.ents[0].label_ == "CONDITION"

    def test_add_rule_regex(self):
        matcher = TargetMatcher(nlp)
        matcher.add([TargetRule("PE", "CONDITION", pattern="pulmonary embolisms?")])
        doc = nlp("Past Medical History: Pulmonary embolism")
        matcher(doc)
        assert len(doc.ents) == 1
        assert (doc.ents[0].start, doc.ents[0].end) == (4, 6)
        assert doc.ents[0].label_ == "CONDITION"

    def test_span_group(self):
        matcher = TargetMatcher(nlp, result_type="group")
        matcher.add([TargetRule("PE", "CONDITION", pattern=[{"LOWER": "pe"}])])
        doc = nlp("Past Medical History: Pe")
        matcher(doc)
        assert len(doc.spans["medspacy_spans"]) == 1
        span = doc.spans["medspacy_spans"][0]
        assert (span.start, span.end) == (4, 5)
        assert span.label_ == "CONDITION"

    def test_custom_span_group(self):
        matcher = TargetMatcher(nlp, result_type="group", span_group_name="test_group")
        matcher.add([TargetRule("PE", "CONDITION", pattern=[{"LOWER": "pe"}])])
        doc = nlp("Past Medical History: Pe")
        matcher(doc)
        assert len(doc.spans["test_group"]) == 1
        span = doc.spans["test_group"][0]
        assert (span.start, span.end) == (4, 5)
        assert span.label_ == "CONDITION"

    def test_pipeline_initiate(self):
        nlp2 = spacy.blank("en")
        nlp2.add_pipe("medspacy_target_matcher")
        assert "medspacy_target_matcher" in nlp2.pipe_names
