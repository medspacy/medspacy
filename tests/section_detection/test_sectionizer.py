import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
import json

import spacy
import warnings
import pytest

from os import path
from pathlib import Path

import medspacy
from medspacy.section_detection import Sectionizer
from medspacy.section_detection import SectionRule

nlp = spacy.load("en_core_web_sm")


class TestSectionizer:
    def test_initiate(self):
        assert Sectionizer(nlp)

    def test_initiate_no_patterns(self):
        assert Sectionizer(nlp, rules=None)

    def test_doc_attributes(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        assert len(doc._.sections)
        assert len(doc._.section_categories)
        assert len(doc._.section_titles)
        assert len(doc._.section_spans)
        assert len(doc._.section_bodies)

    def test_span_attributes(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        span = doc[2:5]

        assert span._.section
        assert len(span._.section_category)
        assert len(span._.section_title)
        assert len(span._.section_span)
        assert len(span._.section_body)
        assert span._.section_rule

    def test_token_attributes(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        token = doc[-1]

        assert token._.section
        assert len(token._.section_category)
        assert len(token._.section_title)
        assert len(token._.section_span)
        assert len(token._.section_body)
        assert token._.section_rule

    def test_section(self):
        sectionizer = Sectionizer(nlp, rules=None)
        rule = SectionRule(
            category="past_medical_history", literal="Past Medical History:"
        )
        sectionizer.add(rule)
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        section = doc._.sections[0]
        assert section.category == "past_medical_history"
        assert doc[section.section_span[0] : section.section_span[1]] == doc[0:]
        assert doc[section.title_span[0] : section.title_span[1]] == doc[0:-1]
        assert doc[section.body_span[0] : section.body_span[1]] == doc[-1:]
        assert section.parent is None
        assert section.rule is rule

    def test_span_attributes3(self):
        sectionizer = Sectionizer(nlp, rules=None)
        rule = SectionRule(
            category="past_medical_history", literal="Past Medical History:"
        )
        sectionizer.add(rule)
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        span = doc[-1:]
        assert span._.section is doc._.sections[0]
        assert span._.section_category == "past_medical_history"
        assert span._.section_span == doc[0:]
        assert span._.section_title == doc[0:-1]
        assert span._.section_body == doc[-1:]
        assert span._.section_parent is None
        assert span._.section_rule is rule

    def test_num_sections(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        assert len(doc._.sections) == 1
        # Now reprocess and make sure it resets
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        assert len(doc._.sections) == 1

    def test_string_match(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        section = doc._.sections[0]
        assert section.category == "past_medical_history"
        assert (
            doc[section.title_span[0] : section.title_span[1]].text
            == "Past Medical History:"
        )
        assert (
            doc[section.section_span[0] : section.section_span[1]].text
            == "Past Medical History: PE"
        )

        # def test_list_pattern_match(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            SectionRule(
                category="past_medical_history",
                literal="past medical history:",
                pattern=[
                    {"LOWER": "past"},
                    {"LOWER": "medical"},
                    {"LOWER": "history"},
                    {"LOWER": ":"},
                ],
            )
        )
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        section = doc._.sections[0]
        assert section.category == "past_medical_history"
        assert (
            doc[section.title_span[0] : section.title_span[1]].text
            == "Past Medical History:"
        )
        assert (
            doc[section.section_span[0] : section.section_span[1]].text
            == "Past Medical History: PE"
        )

    def test_document_starts_no_header(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        doc = nlp("This is separate. Past Medical History: PE")
        sectionizer(doc)
        assert len(doc._.sections) == 2
        section = doc._.sections[0]
        assert section.category is None
        assert doc[section.title_span[0] : section.title_span[1]].text == ""
        assert (
            doc[section.section_span[0] : section.section_span[1]].text
            == "This is separate."
        )

        section = doc._.sections[1]
        assert section.category == "past_medical_history"
        assert (
            doc[section.title_span[0] : section.title_span[1]].text
            == "Past Medical History:"
        )
        assert (
            doc[section.section_span[0] : section.section_span[1]].text
            == "Past Medical History: PE"
        )

    def test_max_scope_none(self):
        sectionizer = Sectionizer(nlp, rules=None, max_section_length=None)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        doc = nlp("Past Medical History: This is the sentence.")
        sectionizer(doc)
        assert doc[-1]._.section_category == "past_medical_history"

    def test_max_scope(self):
        sectionizer = Sectionizer(nlp, rules=None, max_section_length=2)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        doc = nlp("Past Medical History: This is the sentence.")
        sectionizer(doc)
        section = doc._.sections[0]
        assert doc[5]._.section_category == "past_medical_history"
        # This should be out of range of the section scope
        assert doc[-1]._.section_category is None

    def test_max_scope_rule(self):
        sectionizer = Sectionizer(nlp, rules=None, max_section_length=2)
        sectionizer.add(
            SectionRule(
                category="past_medical_history",
                literal="Past Medical History:",
                max_scope=100,
            )
        )
        doc = nlp("Past Medical History: This is the sentence.")
        sectionizer(doc)
        section = doc._.sections[-1]
        token = doc[-1]
        assert section.category == "past_medical_history"
        assert token in doc[section.section_span[0] : section.section_span[1]]
        assert token._.section_category == "past_medical_history"

    def test_start_line(self):
        sectionizer = Sectionizer(nlp, rules=None, require_start_line=True)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        text = "\n\n Past Medical History: The patient has a Past Medical History:"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2

    def test_end_line(self):
        sectionizer = Sectionizer(nlp, rules=None, require_end_line=True)
        sectionizer.add(
            SectionRule(
                category="past_medical_history", literal="Past Medical History:"
            )
        )
        text = (
            "\n\n Past Medical History:\n The patient has a Past Medical History: this"
        )
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2

    def test_parent_section(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(
                    category="past_medical_history", literal="Past Medical History:"
                ),
                SectionRule(
                    category="explanation",
                    literal="Explanation:",
                    parents=["past_medical_history"],
                ),
            ]
        )
        text = "Past Medical History: some other text Explanation: The patient has one"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2
        pmh = doc._.sections[0]
        explanation = doc._.sections[1]
        assert pmh.parent is None
        assert explanation.parent.category == "past_medical_history"

    def test_parent_section_multiple_candidates(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(
                    category="past_medical_history", literal="Past Medical History:"
                ),
                SectionRule(
                    category="explanation",
                    literal="Explanation:",
                    parents=["past_medical_history", "allergies"],
                ),
            ]
        )
        text = "Past Medical History: some other text. Explanation: The patient has one"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2
        pmh = doc._.sections[0]
        explanation = doc._.sections[1]
        assert pmh.parent is None
        assert explanation.parent.category == "past_medical_history"

    def test_parent_section_candidate_after_section(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(
                    category="past_medical_history", literal="Past Medical History:"
                ),
                SectionRule(category="allergies", literal="Allergies:"),
                SectionRule(
                    category="explanation",
                    literal="Explanation:",
                    parents=["past_medical_history", "allergies"],
                ),
            ]
        )
        text = "Past Medical History: some other text. Explanation: The patient has one. Allergies: peanuts"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 3
        pmh = doc._.sections[0]
        explanation = doc._.sections[1]
        allergies = doc._.sections[2]
        assert pmh.parent is None
        assert explanation.parent.category == "past_medical_history"
        assert allergies.parent is None

    def test_parent_section_duplicate_sections_different_parents(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(
                    category="past_medical_history", literal="Past Medical History:"
                ),
                SectionRule(category="allergies", literal="Allergies:"),
                SectionRule(
                    category="explanation",
                    literal="Explanation:",
                    parents=["past_medical_history", "allergies"],
                ),
            ]
        )
        text = "Past Medical History: some other text. Explanation: The patient has one. Allergies: peanuts Explanation: pt cannot eat peanuts"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 4
        pmh = doc._.sections[0]
        explanation = doc._.sections[1]
        allergies = doc._.sections[2]
        explanation2 = doc._.sections[3]
        assert pmh.parent is None
        assert explanation.parent.category == "past_medical_history"
        assert allergies.parent is None
        assert explanation2.parent.category == "allergies"

    def test_parent_section_no_valid_parent(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(
                    category="past_medical_history", literal="Past Medical History:"
                ),
                SectionRule(category="allergies", literal="Allergies:"),
                SectionRule(
                    category="explanation",
                    literal="Explanation:",
                    parents=["past_medical_history"],
                ),
            ]
        )
        text = "Past Medical History: some other text. Allergies: peanuts Explanation: pt cannot eat peanuts"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 3
        pmh = doc._.sections[0]
        allergies = doc._.sections[1]
        explanation = doc._.sections[2]
        assert pmh.parent is None
        assert allergies.parent is None
        assert explanation.parent is None

    def test_parent_section_parent_required(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(
                    category="past_medical_history", literal="Past Medical History:"
                ),
                SectionRule(
                    category="explanation",
                    literal="Explanation:",
                    parents=["past_medical_history"],
                    parent_required=True,
                ),
            ]
        )
        text = "other text Explanation: The patient has one"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 1
        section = doc._.sections[0]
        print(section)
        assert section.category is None
        assert section.parent is None

    def test_parent_section_chain(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(category="s1", literal="section 1:"),
                SectionRule(category="s2", literal="section 2:", parents=["s1"]),
                SectionRule(category="s3", literal="section 3:", parents=["s2"]),
            ]
        )
        text = "section 1: abc section 2: abc section 3: abc"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 3
        s1 = doc._.sections[0]
        s2 = doc._.sections[1]
        s3 = doc._.sections[2]
        assert s1.parent is None
        assert s2.parent.category == "s1"
        assert s3.parent.category == "s2"

    def test_parent_section_chain_backtracking(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(category="s1", literal="section 1:"),
                SectionRule(category="s2", literal="section 2:", parents=["s1"]),
                SectionRule(category="s3", literal="section 3:", parents=["s2"]),
                SectionRule(category="s4", literal="section 4:", parents=["s1"]),
            ]
        )
        text = "section 1: abc section 2: abc section 3: abc section 4: abc"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 4
        s1 = doc._.sections[0]
        s2 = doc._.sections[1]
        s3 = doc._.sections[2]
        s4 = doc._.sections[3]
        assert s1.parent is None
        assert s2.parent.category == "s1"
        assert s3.parent.category == "s2"
        assert s4.parent.category == "s1"

    def test_parent_section_chain_backtracking_interrupted(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(category="s1", literal="section 1:"),
                SectionRule(category="s2", literal="section 2:", parents=["s1"]),
                SectionRule(category="s3", literal="section 3:", parents=["s2"]),
                SectionRule(category="s4", literal="section 4:", parents=["s1"]),
                SectionRule(category="break", literal="section break:"),
            ]
        )
        text = "section 1: abc section 2: abc section 3: abc section break: abc section 4: abc"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 5
        s1 = doc._.sections[0]
        s2 = doc._.sections[1]
        s3 = doc._.sections[2]
        s4 = doc._.sections[4]
        assert s1.parent is None
        assert s2.parent.category == "s1"
        assert s3.parent.category == "s2"
        assert s4.parent is None

    # @pytest.mark.skip("This test fails frequently with new versions") # seems to have been resolved
    def test_duplicate_parent_definitions(self):
        with warnings.catch_warnings(record=True) as w:
            sectionizer = Sectionizer(nlp, rules=None)
            sectionizer.add(
                [
                    SectionRule(category="s1", literal="section 1:"),
                    SectionRule(category="s2", literal="section 2:", parents=["s1"]),
                    SectionRule(category="s2", literal="section 2:", parents=["s3"]),
                    SectionRule(category="s3", literal="section 3:"),
                ]
            )
            text = "section 1: abc section 2: abc section 3: abc section 2: abc"
            doc = nlp(text)
            sectionizer(doc)
            assert len(doc._.sections) == 4
            s1 = doc._.sections[0]
            s2 = doc._.sections[1]
            s3 = doc._.sections[2]
            s2_2 = doc._.sections[3]
            # assert len(w) == 1 # this throws errors if warnings occur elsewhere. check that specific warning is in
            # the buffer instead
            warning_found = False
            for warn in w:
                print("Duplicate" in str(warn.message))
                if (
                    warn.category is RuntimeWarning
                    and "Duplicate section title" in str(warn.message)
                ):
                    warning_found = True
            assert warning_found
            assert s1.parent is None
            assert s2.parent.category == "s1"
            assert s3.parent is None
            assert s2_2.parent.category == "s3"

    def test_attributes_ents(self):
        sectionizer = Sectionizer(
            nlp,
            rules=None,
            span_attrs={"past_medical_history": {"is_historical": True}},
        )
        sectionizer.add([SectionRule("Past Medical History:", "past_medical_history")])
        doc = nlp("Past Medical History: Pneumonia, stroke, and cancer")
        from spacy.tokens import Span

        doc.ents = (Span(doc, 4, 5, "CONDITION"),)
        doc.spans["medspacy_spans"] = (Span(doc, 5, 6, "CONDITION"),)
        doc.spans["test"] = (Span(doc, 6, 7, "CONDITION"),)

        sectionizer(doc)
        assert doc.ents[0]._.is_historical is True
        assert doc.spans["medspacy_spans"][0]._.is_historical is False
        assert doc.spans["test"][0]._.is_historical is False

    def test_attributes_span_groups(self):
        sectionizer = Sectionizer(
            nlp,
            rules=None,
            input_span_type="group",
            span_attrs={"past_medical_history": {"is_historical": True}},
        )
        sectionizer.add([SectionRule("Past Medical History:", "past_medical_history")])
        doc = nlp("Past Medical History: Pneumonia, stroke, and cancer")
        from spacy.tokens import Span

        doc.ents = (Span(doc, 4, 5, "CONDITION"),)
        doc.spans["medspacy_spans"] = (Span(doc, 5, 6, "CONDITION"),)
        doc.spans["test"] = (Span(doc, 6, 7, "CONDITION"),)

        sectionizer(doc)
        assert doc.ents[0]._.is_historical is False
        assert doc.spans["medspacy_spans"][0]._.is_historical is True
        assert doc.spans["test"][0]._.is_historical is False

    def test_attributes_custom_span_groups(self):
        sectionizer = Sectionizer(
            nlp,
            rules=None,
            input_span_type="group",
            span_group_name="test",
            span_attrs={"past_medical_history": {"is_historical": True}},
        )
        sectionizer.add([SectionRule("Past Medical History:", "past_medical_history")])
        doc = nlp("Past Medical History: Pneumonia, stroke, and cancer")
        from spacy.tokens import Span

        doc.ents = (Span(doc, 4, 5, "CONDITION"),)
        doc.spans["medspacy_spans"] = (Span(doc, 5, 6, "CONDITION"),)
        doc.spans["test"] = (Span(doc, 6, 7, "CONDITION"),)

        sectionizer(doc)
        assert doc.ents[0]._.is_historical is False
        assert doc.spans["medspacy_spans"][0]._.is_historical is False
        assert doc.spans["test"][0]._.is_historical is True

    def test_section_categories(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add([SectionRule("Past Medical History:", "past_medical_history")])
        assert sectionizer.section_categories == {"past_medical_history"}

    def test_pipeline_initiate(self):
        nlp2 = spacy.blank("en")
        nlp2.add_pipe("medspacy_sectionizer")
        assert "medspacy_sectionizer" in nlp2.pipe_names

    def test_pipeline_initiate_with_rules(self):
        nlp2 = spacy.blank("en")
        rules = path.join(
            Path(__file__).resolve().parents[2],
            "resources",
            "section_patterns.json",
        )
        sectionizer = nlp2.add_pipe("medspacy_sectionizer", config={"rules": rules})
        assert "medspacy_sectionizer" in nlp2.pipe_names
        assert len(sectionizer.rules) > 0
