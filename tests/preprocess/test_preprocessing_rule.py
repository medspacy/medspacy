import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
from medspacy.preprocess import PreprocessingRule
import pytest
import re

import tempfile

tmpdirname = tempfile.TemporaryDirectory()


class TestMedSpaCyExtensions:
    def test_init_str(self):
        rule = PreprocessingRule("this is a string")
        assert rule.pattern == re.compile("this is a string", re.IGNORECASE)

    def test_call(self):
        rule = PreprocessingRule("COVID-19 SCREENING:")
        text = "COVID-19 SCREENING:"
        preprocessed = rule(text)
        assert preprocessed == ""

    def test_call_repl(self):
        rule = PreprocessingRule("Past medical hx", "Past Medical History")
        text = "The pt has a past medical hx of diabetes."
        preprocessed = rule(text)
        assert preprocessed == "The pt has a Past Medical History of diabetes."

    def test_to_dict(self):
        rule = PreprocessingRule("this is a string")
        d = rule.to_dict()
        assert d == {"pattern": "this is a string", "flags": 34, "repl": "", "callback": None, "desc": None}

    def test_from_dict(self):
        d = {"pattern": "this is a string", "repl": "", "callback": None, "desc": "", "flags": re.IGNORECASE}
        rule = PreprocessingRule.from_dict(d)

    def test_from_json(self):
        import os, json

        dname = os.path.join(tmpdirname.name, "test_preprocess_rules.json")
        # dname = os.path.join(".", "test_preprocess_rules.json")
        data = {
            "preprocessing_rules": [
                {"pattern": "this is a string", "repl": "", "flags": re.IGNORECASE, "ignorecase": True, "callback": None, "desc": ""}
            ]
        }

        with open(dname, "w") as f:
            json.dump(data, f)

        rules = PreprocessingRule.from_json(dname)
        rule = rules[0]
        assert isinstance(rule, PreprocessingRule)
        assert rule.pattern.pattern == "this is a string"
        assert rule.repl == ""
        assert rule.callback is None
        assert rule.desc == ""

    def test_repr(self):
        rule = PreprocessingRule("this is a string")
        print(rule)
