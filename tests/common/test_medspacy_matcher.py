import spacy
import warnings

from medspacy.common.medspacy_matcher import MedspacyMatcher
from medspacy.common import BaseRule

nlp = spacy.blank("en")


class TestTargetMatcher:
    def test_initiate(self):
        assert MedspacyMatcher(nlp)

    def test_add(self):
        matcher = MedspacyMatcher(nlp)
        matcher.add([BaseRule("pneumonia", "CONDITION")])
        assert matcher._rules

    def test_prune_overlapping_matching(self):
        matcher = MedspacyMatcher(nlp, prune=True)
        matcher.add(
            [
                BaseRule("history of", "HISTORICAL"),
                BaseRule("no history of", "NEGATED_EXISTENCE"),
            ]
        )
        doc = nlp("no history of pneumonia")
        matches = matcher(doc)
        assert len(matches) == 1
        _, start, end = matches[0]
        assert doc[start:end].text == "no history of"

    def test_prune_false(self):
        matcher = MedspacyMatcher(nlp, prune=False)
        matcher.add(
            [
                BaseRule("history of", "HISTORICAL"),
                BaseRule("no history of", "NEGATED_EXISTENCE"),
            ]
        )
        doc = nlp("no history of pneumonia")
        matches = matcher(doc)
        assert len(matches) == 2



