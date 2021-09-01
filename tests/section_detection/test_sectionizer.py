import spacy
import warnings
import pytest

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
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        assert len(doc._.sections)
        assert len(doc._.section_categories)
        assert len(doc._.section_titles)
        assert len(doc._.section_spans)
        assert len(doc._.section_bodies)

    def test_span_attributes(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        span = doc[2:5]

        assert len(span._.section)
        assert len(span._.section_category)
        assert len(doc._.section_title)
        assert len(doc._.section_span)
        assert len(doc._.section_body)
        assert len(doc._.section_rule)

    def test_span_attributes(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        token = doc[-1]

        assert len(token._.section)
        assert len(token._.section_category)
        assert len(token._.section_title)
        assert len(token._.section_span)
        assert len(token._.section_body)
        assert len(token._.section_rule)

    def test_section(self):
        sectionizer = Sectionizer(nlp, rules=None)
        rule = SectionRule(category="past_medical_history", literal="Past Medical History:")
        sectionizer.add(rule)
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        section = doc._.sections[0]
        assert section.category == "past_medical_history"
        assert section.section_span == doc[0:]
        assert section.title_span == doc[0:-1]
        assert section.body_span == doc[-1:]
        assert section.parent is None
        assert section.rule is rule

    def test_token_attributes(self):
        sectionizer = Sectionizer(nlp, rules=None)
        rule = SectionRule(category="past_medical_history", literal="Past Medical History:")
        sectionizer.add(rule)
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)

        token = doc[-1]
        assert token._.section is doc._.sections[0]
        assert token._.section_category == "past_medical_history"
        assert token._.section_span == doc[0:]
        assert token._.section_title == doc[0:-1]
        assert token._.section_body == doc[-1:]
        assert token._.section_parent is None
        assert token._.section_rule is rule

    def test_span_attributes(self):
        sectionizer = Sectionizer(nlp, rules=None)
        rule = SectionRule(category="past_medical_history", literal="Past Medical History:")
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


    # def test_load_default_rules(self):
    #     sectionizer = Sectionizer(nlp, rules="default")
    #     assert sectionizer.rules

    # def test_load_no_rules(self):
    #     sectionizer = Sectionizer(nlp, rules=None)
    #     assert sectionizer.rules == []

    # def test_add(self):
    #     sectionizer = Sectionizer(nlp, rules=None)
    #     sectionizer.add([{"section_title": "section", "pattern": "my pattern"}])
    #     assert sectionizer.rules

    def test_num_sections(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        assert len(doc._.sections) == 1
        # Now reprocess and make sure it resets
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        assert len(doc._.sections) == 1

    def test_string_match(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        section = doc._.sections[0]
        assert section.category == "past_medical_history"
        assert section.title_span.text == "Past Medical History:"
        assert section.section_span.text == "Past Medical History: PE"

        # def test_list_pattern_match(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            SectionRule(
                category="past_medical_history",
                literal="past medical history:",
                pattern=[{"LOWER": "past"}, {"LOWER": "medical"}, {"LOWER": "history"}, {"LOWER": ":"}],
            )
        )
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        section = doc._.sections[0]
        assert section.category == "past_medical_history"
        assert section.title_span.text == "Past Medical History:"
        assert section.section_span.text == "Past Medical History: PE"

    def test_document_starts_no_header(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        doc = nlp("This is separate. Past Medical History: PE")
        sectionizer(doc)
        assert len(doc._.sections) == 2
        section = doc._.sections[0]
        assert section.category is None
        assert section.title_span.text == ""
        assert section.body_span.text == "This is separate."

        section = doc._.sections[1]
        assert section.category == "past_medical_history"
        assert section.title_span.text == "Past Medical History:"
        assert section.section_span.text == "Past Medical History: PE"

    def test_max_scope_none(self):
        sectionizer = Sectionizer(nlp, rules=None, max_scope=None)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        doc = nlp("Past Medical History: This is the sentence.")
        sectionizer(doc)
        assert doc[-1]._.section_category == "past_medical_history"


    def test_max_scope(self):
        sectionizer = Sectionizer(nlp, rules=None, max_scope=2)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        doc = nlp("Past Medical History: This is the sentence.")
        sectionizer(doc)
        section = doc._.sections[0]
        assert section.body_span[0]._.section_category == "past_medical_history"
        # This should be out of range of the section scope
        assert doc[-1]._.section_category is None

    def test_max_scope_rule(self):
        sectionizer = Sectionizer(nlp, rules=None, max_scope=2)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:", max_scope=100))
        doc = nlp("Past Medical History: This is the sentence.")
        sectionizer(doc)
        section = doc._.sections[-1]
        token = doc[-1]
        assert section.category == "past_medical_history"
        assert token in section.section_span
        assert token._.section_category == "past_medical_history"

    def test_start_line(self):
        sectionizer = Sectionizer(nlp, rules=None, require_start_line=True)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        text = "\n\n Past Medical History: The patient has a Past Medical History:"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2

    def test_end_line(self):
        sectionizer = Sectionizer(nlp, rules=None, require_end_line=True)
        sectionizer.add(SectionRule(category="past_medical_history", literal="Past Medical History:"))
        text = "\n\n Past Medical History:\n The patient has a Past Medical History: this"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2

    def test_parent_section(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add(
            [
                SectionRule(category="past_medical_history", literal="Past Medical History:"),
                SectionRule(category="explanation", literal="Explanation:", parents=["past_medical_history"]),
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
                SectionRule(category="past_medical_history", literal="Past Medical History:"),
                SectionRule(category="explanation", literal="Explanation:", parents=["past_medical_history", "allergies"]),
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
                SectionRule(category="past_medical_history", literal="Past Medical History:"),
                SectionRule(category="allergies", literal="Allergies:"),
                SectionRule(category="explanation", literal="Explanation:", parents=["past_medical_history", "allergies"]),
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
                SectionRule(category="past_medical_history", literal="Past Medical History:"),
                SectionRule(category="allergies", literal="Allergies:"),
                SectionRule(category="explanation", literal="Explanation:", parents=["past_medical_history", "allergies"]),
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
                SectionRule(category="past_medical_history", literal="Past Medical History:"),
                SectionRule(category="allergies", literal="Allergies:"),
                SectionRule(category="explanation", literal="Explanation:", parents=["past_medical_history"]),
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
                SectionRule(category="past_medical_history", literal="Past Medical History:"),
                SectionRule(
                    category="explanation", literal="Explanation:", parents=["past_medical_history"], parent_required=True
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

    @pytest.mark.skip("This test fails frequently with new versions")
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
            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)
            assert s1.parent is None
            assert s2.parent.category == "s1"
            assert s3.parent is None
            assert s2_2.parent.category == "s3"

    def test_context_attributes(self):
        sectionizer = Sectionizer(nlp, rules=None, add_attrs={"past_medical_history": {"is_negated": True}})
        sectionizer.add([SectionRule("Past Medical History:", "past_medical_history")])
        doc = nlp("Past Medical History: Pneumonia")
        from spacy.tokens import Span
        doc.ents = (Span(doc, 4, 5, "CONDITION"),)
        sectionizer(doc)
        assert doc.ents[0]._.is_negated is True

    def test_section_categories(self):
        sectionizer = Sectionizer(nlp, rules=None)
        sectionizer.add([SectionRule("Past Medical History:", "past_medical_history")])
        assert sectionizer.section_categories == ["past_medical_history"]
