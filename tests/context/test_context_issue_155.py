"""Regression tests for https://github.com/medspacy/medspacy/issues/155.

The BACKWARD ": no" modifier rule used to win modifier-overlap pruning over an
overlapping FORWARD "no" rule and then modify nothing, so entities like the
one in "FINDINGS: No pneumonia" were never negated. Modifier overlap pruning
now happens after modifiers are linked to targets, preferring the modifier
which modified more targets.

These tests are hermetic: they use spacy.blank("en") with no model downloads.
"""
import spacy
from spacy.tokens import Span

import medspacy  # noqa: F401  (registers the medspacy_context factory)
from medspacy.context import ConTextRule


def make_nlp(rules=None, **context_kwargs):
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    kwargs = {"match_target_sents_only": False}
    kwargs.update(context_kwargs)
    context = nlp.add_pipe("medspacy_context", config=kwargs)
    if rules:
        context.add(rules)
    return nlp, context


def process(nlp, context, text, ent_spans):
    doc = nlp(text)
    doc.ents = [Span(doc, start, end, label="FINDING") for (start, end) in ent_spans]
    return context(doc)


def modifier_texts(doc):
    return [
        doc[m.modifier_span[0] : m.modifier_span[1]].text
        for m in doc._.context_graph.modifiers
    ]


def test_colon_no_negates_following_entity():
    """ryleyb's example: 'FINDINGS: No pneumonia' should negate pneumonia."""
    nlp, context = make_nlp()
    # FINDINGS(0) :(1) No(2) pneumonia(3)
    doc = process(nlp, context, "FINDINGS: No pneumonia", [(3, 4)])
    assert doc.ents[0]._.is_negated is True
    assert modifier_texts(doc) == ["No"]


def test_no_further_rule_with_and_without_header():
    """The issue reporter's example: a FORWARD 'no further' rule must negate
    the entity whether or not a section header precedes it."""
    rules = [
        ConTextRule(
            literal=None,
            pattern=[{"LOWER": "no"}, {"LOWER": "further"}],
            category="NEGATED_EXISTENCE",
            direction="FORWARD",
        )
    ]
    nlp, context = make_nlp(rules)
    # No(0) further(1) ischemic(2) evaluation(3) warranted(4) .(5)
    doc = process(
        nlp, context, "No further ischemic evaluation warranted.", [(2, 4)]
    )
    assert doc.ents[0]._.is_negated is True
    # RECOMMENDATION(0) AND(1) SUGGESTIONS(2) :(3) No(4) further(5) ischemic(6)
    # evaluation(7) warranted(8) .(9)
    doc = process(
        nlp,
        context,
        "RECOMMENDATION AND SUGGESTIONS: No further ischemic evaluation warranted.",
        [(6, 8)],
    )
    assert doc.ents[0]._.is_negated is True


def test_colon_no_before_entity_list():
    """firejake308's example: 'Vision: no visual changes, blurry vision, or
    double vision' should negate 'blurry vision', not the header."""
    nlp, context = make_nlp()
    # Vision(0) :(1) no(2) visual(3) changes(4) ,(5) blurry(6) vision(7) ,(8)
    # or(9) double(10) vision(11)
    doc = process(
        nlp,
        context,
        "Vision: no visual changes, blurry vision, or double vision",
        [(6, 8)],
    )
    assert doc.ents[0]._.is_negated is True
    assert modifier_texts(doc) == ["no"]


def test_qa_style_backward_no_still_negates():
    """jianlins' counter-example: in Q&A style text ('pain: no'), the BACKWARD
    ': no' modifier must still negate the entity to its left."""
    nlp, context = make_nlp()
    # pain(0) :(1) no(2)
    doc = process(nlp, context, "pain: no", [(0, 1)])
    assert doc.ents[0]._.is_negated is True
    assert modifier_texts(doc) == [": no"]


def test_prune_false_keeps_overlapping_modifiers():
    """With prune_on_modifier_overlap=False, both overlapping modifiers survive."""
    nlp, context = make_nlp(prune_on_modifier_overlap=False)
    doc = process(nlp, context, "FINDINGS: No pneumonia", [(3, 4)])
    assert sorted(modifier_texts(doc)) == sorted([": No", "No"])
