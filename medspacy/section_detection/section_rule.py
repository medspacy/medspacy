from ..common.base_rule import BaseRule


class SectionRule(BaseRule):

    _ALLOWED_KEYS = {"literal", "pattern", "category", "metadata", "parents", "parent_required", "max_scope"}

    def __init__(
        self, literal, category, pattern=None, on_match=None, max_scope=None, parents=[], parent_required=False, metadata=None
    ):
        """Class for defining rules for extracting entities from text using TargetMatcher.
        Params:
            literal (str): The actual string of a concept. If pattern is None,
                this string will be lower-cased and matched to the lower-case string.
                If `pattern` is not None, this argument will not be used for actual matching
                but can be used as a reference as the direction name.
            category (str): The semantic class of the matched span. This corresponds to the `label_`
                attribute of an entity.
            pattern (list, str, or None): A pattern to use for matching rather than `literal`.
                If a list, will use spaCy dictionary pattern matching to match using token attributes.
                See https://spacy.io/usage/rule-based-matching.
                If a string, will use regular expression matching on the underlying text of a doc.
                Note that regular-expression matching is not natively supported by spaCy and could
                result in unexpected matched spans if match boundaries do not align with token boundaries.
                If None, `literal` will be matched exactly.
            on_match (callable or None): An optional callback function or other callable which takes 4 arguments:
                (matcher, doc, i, matches)
                For more information, see https://spacy.io/usage/rule-based-matching#on_match
            max_scope (int or None): A number of tokens to explicitly limit the size of a section body.
                If None, the scope will include the entire doc up until either the next section header or the end
                of the doc. This variable can also be set at a global level as `Sectionizer(nlp, max_scope=...)`,
                but if the attribute is set here, the rule scope will take precedence.
                If not None, this will be the number of tokens following the matched section header
                    Example:
                        In the text "Past Medical History: Pt has hx of pneumonia",
                        SectionRule("Past Medical History:", "pmh", max_scope=None) will include the entire doc, but
                        SectionRule("Past Medical History:", "pmh", max_scope=2) will limit the section
                            to be "Past Medical History: Pt has"
                This can be useful for limiting certain sections which are known to be short or allowing others
                to be longer than the regular global max_scope.
            parents (list or None): a list of candidate parents for determining subsections
            parent_required (bool): whether a parent is required for the section to exist in the final output
            metadata (dict or None): Optional dictionary of metadata.
        """
        super().__init__(literal, category, pattern, on_match, metadata)
        self.max_scope = max_scope
        self.parents = parents
        if parent_required:
            if not parents:
                raise ValueError(
                    "Jsonl file incorrectly formatted for pattern name {0}. If parents are required, then at least one parent must be specified.".format(
                        category
                    )
                )
        self.parent_required = parent_required

    @classmethod
    def from_json(cls, filepath):
        """Read in a lexicon of modifiers from a JSON file.

        Args:
            filepath: the .json file containing modifier rules

        Returns:
            section_rules: a list of SectionRule objects
        Raises:
            KeyError: if the dictionary contains any keys other than
                those accepted by SectionRule.__init__
        """
        import json

        with open(filepath) as file:
            section_data = json.load(file)
        section_rules = []
        for data in section_data["section_rules"]:
            section_rules.append(SectionRule.from_dict(data))
        return section_rules

    @classmethod
    def from_dict(cls, rule_dict):
        """Reads a dictionary into a SectionRule list. Used when reading from a json file.

        Args:
            rule_dict: the dictionary to convert

        Returns:
            item: the SectionRule created from the dictionary

        Raises:
            ValueError: if the json is invalid
        """
        keys = set(rule_dict.keys())
        invalid_keys = keys.difference(cls._ALLOWED_KEYS)
        if invalid_keys:
            msg = "JSON object contains invalid keys: {0}.\n" "Must be one of: {1}".format(invalid_keys, cls._ALLOWED_KEYS)
            raise ValueError(msg)
        rule = SectionRule(**rule_dict)
        return rule

    @classmethod
    def to_json(cls, section_rules, filepath):
        """Writes SectionRules to a json file.

        Args:
            section_rules: a list of SectionRules that will be written to a file.
            filepath: the .json file to contain modifier rules
        """
        import json

        data = {"section_rules": [rule.to_dict() for rule in section_rules]}
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)

    def to_dict(self):
        """Converts TargetRules to a python dictionary. Used when writing section rules to a json file.

        Returns:
            rule_dict: the dictionary containing the TargetRule info.
        """
        rule_dict = {}
        for key in self._ALLOWED_KEYS:
            value = self.__dict__.get(key)
            if value is not None:
                rule_dict[key] = value
        return rule_dict

    def __repr__(self):
        return f"""SectionRule(literal="{self.literal}", category="{self.category}", pattern={self.pattern}, on_match={self.on_match}, parents={self.parents}, parent_required={self.parent_required})"""
