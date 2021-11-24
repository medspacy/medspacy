import warnings
import pytest
import re

from medspacy.section_detection.util import create_regex_pattern_from_section_name
class TestSectionizerUtils:
    @pytest.mark.parametrize("section_name, section_text", [("past medical history", "Past Medical History:"), ("past medical history", "Past Medical History   -"), ("past medical history", "Past Medical      History:"), ("past medical history", "PAST MEDICAL HISTORY\n")])
    def test_create_regex_simple_positive(self, section_name, section_text):
        regex = re.compile(create_regex_pattern_from_section_name(section_name))
        assert regex.match(section_text)[0] == section_text
    
    @pytest.mark.parametrize("section_name, section_text", [("past medical history", "Past Medical History: *stuff"), ("past medical history", "Past Medical History   - *stuff"), ("past medical history", "Past Medical      History: *stuff"), ("past medical history", "PAST MEDICAL HISTORY\n *stuff")])
    def test_create_regex_simple_negative(self, section_name, section_text):
        regex = re.compile(create_regex_pattern_from_section_name(section_name))
        assert len(regex.match(section_text)[0]) + len(" *stuff") == len(section_text)