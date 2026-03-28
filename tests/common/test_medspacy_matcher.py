import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
import spacy
import warnings
from spacy.matcher import Matcher, PhraseMatcher

from medspacy.common.medspacy_matcher import MedspacyMatcher
from medspacy.common.regex_matcher import RegexMatcher
from medspacy.common import BaseRule

nlp = spacy.blank("en")
nlp.add_pipe("sentencizer")


class TestTargetMatcher:
    def test_initiate(self):
        assert MedspacyMatcher(nlp)

    def test_add(self):
        matcher = MedspacyMatcher(nlp)
        matcher.add([BaseRule("pneumonia", "CONDITION")])
        assert matcher.rules

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


class TestSpacyMatcherSpanIndices:
    """Verify that spaCy's Matcher, PhraseMatcher, and RegexMatcher return
    the expected index coordinate systems when called on a Span.

    These tests document spaCy's behavior so that if it changes in a future
    version, the test suite will catch it immediately. MedspacyMatcher
    depends on normalizing these differences.

    As of spaCy 3.7:
    - Matcher returns span-relative indices
    - PhraseMatcher returns doc-relative indices
    - RegexMatcher (medspaCy) returns doc-relative indices
    """

    def _make_doc(self):
        doc = nlp("No pneumonia. Possible pneumonia.")
        sents = list(doc.sents)
        assert len(sents) == 2
        return doc, sents[0], sents[1]

    def test_spacy_matcher_returns_span_relative_indices(self):
        """spaCy Matcher returns indices relative to the Span, not the Doc."""
        doc, sent1, sent2 = self._make_doc()

        matcher = Matcher(nlp.vocab)
        matcher.add("POSSIBLE", [[{"LOWER": "possible"}]])

        # On full doc: should return doc-relative index 3
        doc_matches = matcher(doc)
        assert len(doc_matches) == 1
        assert doc_matches[0][1] == 3  # start index

        # On second sentence: returns span-relative index 0
        sent_matches = matcher(sent2)
        assert len(sent_matches) == 1
        assert sent_matches[0][1] == 0  # span-relative, NOT 3

    def test_spacy_phrase_matcher_returns_doc_relative_indices(self):
        """spaCy PhraseMatcher returns doc-relative indices even on a Span."""
        doc, sent1, sent2 = self._make_doc()

        pm = PhraseMatcher(nlp.vocab, attr="LOWER")
        pm.add("POSSIBLE", [nlp.make_doc("possible")])

        # On second sentence: returns doc-relative index 3
        sent_matches = pm(sent2)
        assert len(sent_matches) == 1
        assert sent_matches[0][1] == 3  # doc-relative

    def test_regex_matcher_returns_doc_relative_indices(self):
        """medspaCy RegexMatcher returns doc-relative indices on a Span."""
        doc, sent1, sent2 = self._make_doc()

        rm = RegexMatcher(nlp.vocab)
        rm.add("POSSIBLE", [r"[Pp]ossible"])

        # On second sentence: returns doc-relative index 3
        sent_matches = rm(sent2)
        assert len(sent_matches) == 1
        assert sent_matches[0][1] == 3  # doc-relative


class TestMedspacyMatcherSpanIndices:
    """Verify that MedspacyMatcher normalizes all match indices to
    doc-relative coordinates, regardless of which internal matcher
    produced the match."""

    def _make_doc(self):
        doc = nlp("No pneumonia. Possible pneumonia.")
        sents = list(doc.sents)
        return doc, sents[0], sents[1]

    def test_phrase_rule_on_span_returns_doc_relative(self):
        """A phrase-based rule matched on a Span returns doc-relative indices."""
        doc, sent1, sent2 = self._make_doc()

        matcher = MedspacyMatcher(nlp)
        matcher.add([BaseRule("possible", "POSSIBLE")])

        matches = matcher(sent2)
        assert len(matches) == 1
        _, start, end = matches[0]
        assert start == 3
        assert end == 4
        assert doc[start:end].text == "Possible"

    def test_token_pattern_rule_on_span_returns_doc_relative(self):
        """A token-pattern rule matched on a Span returns doc-relative indices."""
        doc, sent1, sent2 = self._make_doc()

        matcher = MedspacyMatcher(nlp)
        matcher.add([BaseRule("possible", "POSSIBLE",
                              pattern=[{"LOWER": "possible"}])])

        matches = matcher(sent2)
        assert len(matches) == 1
        _, start, end = matches[0]
        assert start == 3
        assert end == 4
        assert doc[start:end].text == "Possible"

    def test_regex_rule_on_span_returns_doc_relative(self):
        """A regex rule matched on a Span returns doc-relative indices."""
        doc, sent1, sent2 = self._make_doc()

        matcher = MedspacyMatcher(nlp)
        matcher.add([BaseRule("possible", "POSSIBLE",
                              pattern=r"[Pp]ossible")])

        matches = matcher(sent2)
        assert len(matches) == 1
        _, start, end = matches[0]
        assert start == 3
        assert end == 4
        assert doc[start:end].text == "Possible"

    def test_multiple_sents_all_doc_relative(self):
        """Matching on multiple sentences returns doc-relative indices for all."""
        doc, sent1, sent2 = self._make_doc()

        matcher = MedspacyMatcher(nlp)
        matcher.add([BaseRule("pneumonia", "CONDITION")])

        all_matches = []
        for sent in doc.sents:
            all_matches += matcher(sent)

        assert len(all_matches) == 2
        # First match: "pneumonia" at token 1
        assert all_matches[0][1] == 1
        assert all_matches[0][2] == 2
        # Second match: "pneumonia" at token 4
        assert all_matches[1][1] == 4
        assert all_matches[1][2] == 5

    def test_first_sent_indices_unchanged(self):
        """For the first sentence (start=0), indices are the same regardless."""
        doc, sent1, sent2 = self._make_doc()

        matcher = MedspacyMatcher(nlp)
        matcher.add([BaseRule("no", "NEGATION",
                              pattern=[{"LOWER": "no"}])])

        doc_matches = matcher(doc)
        sent_matches = matcher(sent1)

        # Both should return index 0
        assert doc_matches[0][1] == 0
        assert sent_matches[0][1] == 0
