import pytest

from medspacy.section_detection import TextSectionizer


class TestTextSectionizer:
    def test_add(self):
        sectionizer = TextSectionizer(patterns=None)
        sectionizer.add([{"section_title": "section", "pattern": "my pattern"}])
        assert sectionizer.patterns

    def test_add_wo_flag(self):
        sectionizer = TextSectionizer(patterns=None)
        sectionizer.add(
            [{"section_title": "section", "pattern": "my pattern"}], cflags=[]
        )
        assert sectionizer.patterns

    def test_string_match(self):
        sectionizer = TextSectionizer(patterns=None)
        sectionizer.add(
            [
                {
                    "section_title": "past_medical_history",
                    "pattern": "Past Medical History:",
                }
            ]
        )
        doc = "Past Medical History: PE"
        sections = sectionizer(doc)
        (section_title, header, section) = sections[0]
        assert section_title == "past_medical_history"
        assert header == "Past Medical History:"
        assert section == "Past Medical History: PE"

    def test_string_match_case_sensitive(self):
        sectionizer = TextSectionizer(patterns=None)
        sectionizer.add(
            [
                {
                    "section_title": "past_medical_history",
                    "pattern": "PAST MEDICAL HISTORY:",
                }
            ],
            cflags=[],
        )
        doc = "Past Medical History: PE"
        sections = sectionizer(doc)
        (section_title, header, section) = sections[0]
        assert section_title == None
        assert header == None

    def test_string_match_case_sensitive2(self):
        sectionizer = TextSectionizer(patterns=None)
        sectionizer.add(
            [
                {
                    "section_title": "past_medical_history",
                    "pattern": "PAST MEDICAL HISTORY:",
                }
            ],
            cflags=[],
        )
        doc = "PAST MEDICAL HISTORY: PE"
        sections = sectionizer(doc)
        (section_title, header, section) = sections[0]
        assert section_title == "past_medical_history"
        assert header == "PAST MEDICAL HISTORY:"
        assert section == "PAST MEDICAL HISTORY: PE"

        def test_string_match_case_sensitive3(self):
            sectionizer = TextSectionizer(patterns=None)
            sectionizer.add(
                [
                    {
                        "section_title": "past_medical_history",
                        "pattern": "PAST MEDICAL HISTORY:",
                    }
                ],
                cflags=[],
            )
            doc = "PAST MEDICAL HISTORY: PE"
            sections = sectionizer(doc)
            (section_title, header, section) = sections[0]
            assert section_title == "past_medical_history"
            assert header == "Past Medical History:"
            assert section == "Past Medical History: PE"
