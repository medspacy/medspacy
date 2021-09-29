import re


class PreprocessingRule:

    _ALLOWED_KEYS = {"pattern", "repl", "desc", "pattern"}

    def __init__(self, pattern, repl="", ignorecase=True, callback=None, desc=""):
        """Create a new PreprocessingRule. Preprocessing rules define spans of text to be removed and optionally
        replaced from the text underneath a doc.

        Arsg:
            pattern (str or re.Pattern): The text pattern to match and replace in a doc.
                Must be either a string, which will be compiled as a case-insensitive regular expression,
                or a compiled regular expression. The patterns will lead to re.Match objects.
            repl (str or callable): The text to replace a matched string with. By default is an empty string.
                If a callable, then this will be passed into the re.Pattern.sub() method and will be called on
                the match object and return the replacement text. See the re documentation for more examples.
            ignorecase (bool): If pattern is a string, this will indicate whether to compile the pattern with
                re.IGNORECASE.
            callback (None or callable): An optional callable which takes the match and returns the entire text for a new doc,
                rather than just the replacement string for the matched text. This can allow larger text manipulation,
                such as stripping out an entire section based on a header.
            self.desc (str): An optional description.

            For serialization methods such as to_json, repl must be a str and callback is not supported.
        """
        if isinstance(pattern, str):
            if ignorecase is True:
                pattern = re.compile(pattern, flags=re.IGNORECASE)
            else:
                pattern = re.compile(pattern)
        elif not isinstance(pattern, re.Pattern):
            raise ValueError("pattern must be either a str or re.Pattern, not", type(pattern))
        self.pattern = pattern
        self.repl = repl
        self.ignorecase = ignorecase
        self.callback = callback
        self.desc = desc

    @classmethod
    def from_dict(self, d):
        if "flags" in d:
            pattern = re.compile(d["pattern"], flags=d["flags"])
        else:
            pattern = re.compile(d["pattern"])
        return PreprocessingRule(
            pattern,
            repl=d.get("repl"),
            ignorecase=d.get("ignorecase", False),
            callback=d.get("callback"),
            desc=d.get("desc", ""),
        )

    def to_dict(self):
        d = {
            "pattern": self.pattern.pattern,
            "repl": self.repl,
            "callback": self.callback,
            "desc": self.desc,
            "ignorecase": self.ignorecase,
        }
        if self.pattern.flags is not None and self.pattern.flags != 34:  # re.IGNORECASE
            d["flags"] = self.pattern.flags
        return d

    @classmethod
    def from_json(cls, filepath):
        import json

        with open(filepath) as f:
            data = json.load(f)
        return [PreprocessingRule.from_dict(rule) for rule in data["preprocessing_rules"]]

    @classmethod
    def to_json(cls, preprocess_rules, filepath):
        import json

        # Validate that all of the keys are serializable
        dicts = []
        for rule in preprocess_rules:
            if not isinstance(rule.repl, str):
                raise ValueError(
                    "The repl attribute must currently be a string to be serialized as json, not", type(rule.repl)
                )
            if rule.callback is not None:
                raise ValueError("The callback attribute is not serializable and must be left as None.")
            dicts.append(rule.to_dict())
        data = {"preprocessing_rules": dicts}
        with open(filepath, "w") as f:
            json.dump(data, f)

    def __call__(self, text):
        """Apply a preprocessing direction. If the callback attribute of direction is None,
        then it will return a string using the direction pattern.sub method.
        If callback is not None, then then callback function will be executed using
        the the resulting match as an argument.
        """
        # If the direction just has a repl attribute,
        # Just return a simple re.sub
        if self.callback is None:
            return self.pattern.sub(self.repl, text)

        match = self.pattern.search(text)
        if match is None:
            return text
        return self.callback(match)

    def __repr__(self):
        return "PreprocessingRule(pattern={0}, repl={1}, callback={2}, desc={3})".format(
            self.pattern, self.repl, self.callback, self.desc
        )
