from __future__ import annotations

import re
from typing import Union, Optional, Dict, Callable, Any


class PreprocessingRule:
    """
    This is a rule for handling preprocessing in the medspaCy Preprocessor. This class does not inherit from BaseRule,
    as it cannot be used in a spaCy pipeline. The Preprocessor and PreprocessingRules are designed to preprocess text
    before entering a spaCy pipeline to allow for destructive preprocessing, such as stripping or replacing text.
    """

    _ALLOWED_KEYS = {"pattern", "repl", "desc", "pattern", "flags"}

    def __init__(
        self,
        pattern: str,
        repl: Union[str, Callable[[re.Match], Any]] = "",
        flags: re.RegexFlag = re.IGNORECASE,
        callback: Optional[Callable[[str, re.Match], str]] = None,
        desc: Optional[str] = None,
    ):
        """
        Creates a new PreprocessingRule. Preprocessing rules define spans of text to be removed and optionally
        replaced from the text underneath a doc.

        Args:
            pattern: The text pattern to match and replace in a doc. Must be a string, which will be compiled as
                a regular expression. The patterns will lead to re.Match objects.
            repl: The text to replace a matched string with. By default, repl is an empty string. If repl is a function,
                sends function to re.sub and it will be called on each Match object. More info here
                https://docs.python.org/3/library/re.html#re.sub
            flags: A regex compilation flag. Default is re.IGNORECASE.
            callback: An optional callable which takes the raw text and a Match and returns the new copy of the text,
                rather than just replacing strings for the matched text. This can allow larger text manipulation, such
                as stripping out an entire section based on a header.
            desc: An optional description.
        """
        self.pattern = re.compile(pattern, flags=flags)
        self.repl = repl
        self.callback = callback
        self.desc = desc

    @classmethod
    def from_dict(cls, d: Dict) -> PreprocessingRule:
        """
        Creates a PreprocessingRule from a dictionary.

        Args:
            d: The dict to read.

        Returns:
            A PreprocessingRule from the dictionary.
        """
        return PreprocessingRule(
            d["pattern"],
            repl=d["repl"],
            flags=d["flags"],
            callback=d["callback"],
            desc=d.get("desc", None),
        )

    def to_dict(self):
        """
        Writes a preprocessing rule to a dictionary. Useful for writing all rules to a json later.

        Returns:
            A dictionary containing the PreprocessingRule's data.
        """
        d = {
            "pattern": self.pattern.pattern,
            "repl": self.repl,
            "callback": self.callback,
            "desc": self.desc,
            "flags": self.pattern.flags,
        }
        return d

    @classmethod
    def from_json(cls, filepath):
        """
        Read a JSON file containing PreprocessingRule data at the key "preprocessing_rules".

        Args:
            filepath: The filepath of the JSON to read.

        Returns:
            A list of PreprocessingRules from the JSON file.
        """
        import json

        with open(filepath) as f:
            data = json.load(f)
        return [
            PreprocessingRule.from_dict(rule) for rule in data["preprocessing_rules"]
        ]

    def __call__(self, text):
        """
        Apply a preprocessing direction. If the callback attribute of direction is None, then it will return a string
        using the direction sub method. If callback is not None, then callback function will be executed using
        the resulting match as an argument.
        """
        # If the direction just has a repl attribute,
        # Just return a simple re.sub
        if self.callback is None:
            return self.pattern.sub(self.repl, text)

        match = self.pattern.search(text)
        if match is None:
            return text
        return self.callback(text, match)

    def __repr__(self):
        return (
            f"PreprocessingRule(pattern={self.pattern.pattern}, flags={self.pattern.flags}, repl={self.repl}, "
            f"callback={self.callback}, desc={self.desc})"
        )
