import json
from ..common.base_rule import BaseRule

import warnings
warnings.simplefilter('always')



class ConTextRule(BaseRule):
    """A ConTextRule defines a ConText modifier. ConTextRules are rules which define
    which spans are extracted as modifiers and how they behave, such as the phrase to be matched,
    the category/semantic class, the direction of the modifier in the text, and what types of target
    spans can be modfified.
    """

    _ALLOWED_DIRECTIONS = (
        "FORWARD",
        "BACKWARD",
        "BIDIRECTIONAL",
        "TERMINATE",
        "PSEUDO",
    )
    _ALLOWED_KEYS = {
        "literal",
        "direction",
        "pattern",
        "category",
        "metadata",
        "allowed_types",
        "excluded_types",
        "max_targets",
        "max_scope",
    }

    def __init__(
        self,
        literal,
        category,
        direction="BIDIRECTIONAL",
        pattern=None,
        on_match=None,
        on_modifies=None,
        allowed_types=None,
        excluded_types=None,
        max_scope=None,
        max_targets=None,
        terminated_by=None,
        metadata=None,
        filtered_types=None,
        **kwargs
    ):
        """Create an ConTextRule object.
        The primary arguments of `literal` `category`, and `direction` define
        the span of text to be matched, the semantic category, and the direction
        within the sentence in which the modifier operates.
        Other arguments specify additional custom logic such as:
            - Additional control over what text can be matched as a modifier (pattern and on_match)
            - Which types of targets can be modified (allowed_types, excluded_types)
            - The scope size and number of targets that a modifier can modify (max_targets, max_scope)
            - Other logic for terminating a span or for allowing a modifier to modify a target (on_modifies, terminated_by)


        Args:
            literal (str): The actual string of a concept. If pattern is None,
                this string will be lower-cased and matched to the lower-case string.
            category (str): The semantic class of the modifier. Case insensitive.
            pattern (list, str, or None): A pattern to use for matching rather than `literal`.
                If a list, will use spaCy dictionary pattern matching to match using token attributes.
                See https://spacy.io/usage/rule-based-matching.
                If a string, will use regular expression matching on the underlying text of a doc.
                Note that regular-expression matching is not natively supported by spaCy and could
                result in unexpected matched spans if match boundaries do not align with token boundaries.
                If None, `literal` will be matched exactly.
            direction (str): The directionality or action of a modifier. This defines which part
                of a sentence a modifier will include as its scope. Entities within
                the scope will be considered to be modified.
                Valid values are:
                 - "FORWARD": Scope will begin after the end of a modifier and move
                    to the right towards the end of the sentence
                - "BACKWARD": Scope will begin before the beginning of a modifier
                    and move to the left towards the beginning of a sentence
                - "BIDIRECTIONAL": Scope will expand on either side of a modifier
                - "TERMINATE": A special direction to limit any other modifiers
                    if this phrase is in its scope.
                    Example: "no evidence of chf but there is pneumonia":
                        "but" will prevent "no evidence of" from modifying "pneumonia"
                - "PSEUDO": A special direction which will not modify any targets.
                    This can be used for differentiating superstrings of modifiers.
                    Example: A modifier with literal="negative attitude"
                    will prevent the phrase "negative" in "She has a negative attitude about her treatment"
                    from being extracted as a modifier.
            on_match (callable or None): Callback function to act on spaCy matches.
                Takes the argument matcher, doc, i, and matches.
            on_modifies (callable or None): Callback function to run when building an edge
                between a target and a modifier. This allows specifying custom logic for
                allowing or preventing certain modifiers from modifying certain targets.
                The callable should take 3 arguments:
                    target: The spaCy Span from doc.ents (ie., 'Evidence of pneumonia')
                    modifier: The spaCy Span covered in a resulting modifier (ie., 'no evidence of')
                    span_between: The Span between the target and modifier in question.
                Should return either True or False. If returns False, then the modifier will not modify
                the target.
#           allowed_types (set or None): A set of target labels to allow a modifier to modify.
                If None, will apply to any type not specifically excluded in excluded_types.
                Only one of allowed_types and excluded_types can be used. An error will be thrown
                if both are not None.
            excluded_types (set or None): A set of target labels which this modifier cannot modify.
                If None, will apply to all target types unless allowed_types is not None.
            max_scope (int or None): A number of tokens to explicitly limit the size of the modifier's scope.
                If None, the scope will include the entire sentence in the direction of `direction`
                (ie., starting at the beginning of the sentence for "BACKWARD", end of the sentence for "FORWARD",
                and the entire sentence for "BIDIRECTIONAL".
                This is useful for requiring modifiers be very close to a concept in the text
                or for preventing too far of modifier ranges caused by undersplitting of sentences.
                Example: In the sentence "pt with chf, pna vs. rsv", "vs." will modify
                    only "pna" and "rsv" if max_scope=1 and direction="BIDIRECTIONAL".
            max_targets (int or None): The maximum number of targets which a modifier can modify.
                If None, will modify all targets in its scope.
            terminated_by (iterable or None): An optional array of other modifier categories which will
                terminate the scope of this modifier. If None, only "TERMINATE" will do this.
                Example: if a ConTextRule defining "positive for" has terminated_by={"NEGATED_EXISTENCE"},
                then in the sentence "positive for flu, negative for RSV", the positive modifier
                will modify "flu" but will be terminated by "negative for" and will not modify "RSV".
                This helps prevent multiple conflicting modifiers from distributing too far across
                a sentence.
            metadata (dict or None): A dict of additional data to pass in,
                such as free-text comments, additional attributes, or ICD-10 codes.
                Default None.

        Returns:
            direction: a ConTextRule
        """
        super().__init__(literal, category.upper(), pattern, on_match, metadata)
        # 'direction' used to be called 'rule', so we'll handle that here and raise a warning
        if "rule" in kwargs:
            warnings.warn("The 'rule' argument from ConTextItem has been replaced with 'direction' "
                                     "in ConTextRule. In the future please use 'direction': "
                                     "ConTextItem(literal, category, direction=...)",
                          DeprecationWarning)
            self.direction = kwargs["rule"].upper()
        else:
            self.direction = direction.upper()

        self.on_modifies = on_modifies

        if allowed_types is not None and excluded_types is not None:
            raise ValueError(
                "A ConTextRule was instantiated with non-null values for both allowed_types and excluded_types. "
                "Only one of these can be non-null, since cycontext either explicitly includes or excludes target types."
            )
        if allowed_types is not None:
            self.allowed_types = {label.upper() for label in allowed_types}
        else:
            self.allowed_types = None
        if excluded_types is not None:
            self.excluded_types = {label.upper() for label in excluded_types}
        else:
            self.excluded_types = None

        if max_targets is not None and max_targets <= 0:
            raise ValueError("max_targets must be >= 0 or None.")
        self.max_targets = max_targets
        if max_scope is not None and max_scope <= 0:
            raise ValueError("max_scope must be >= 0 or None.")
        self.max_scope = max_scope
        if terminated_by is None:
            terminated_by = set()
        else:
            if isinstance(terminated_by, str):
                raise ValueError(
                    "terminated_by must be an iterable, such as a list or set, not {}.".format(
                        terminated_by
                    )
                )
            terminated_by = {string.upper() for string in terminated_by}

        self.terminated_by = terminated_by

        self.filtered_types = filtered_types

        self.metadata = metadata

        if self.direction not in self._ALLOWED_DIRECTIONS:
            raise ValueError(
                "Direction {0} not recognized. Must be one of: {1}".format(
                    self.direction, self._ALLOWED_DIRECTIONS
                )
            )


    @property
    def rule(self):
        "Deprecated attribute name from ConTextItem. Now `direction`."
        warnings.warn("The 'rule' attribute has been replaced with 'direction'.", DeprecationWarning)
        return self.direction

    @classmethod
    def from_yaml(cls, _file):
        """Read in a lexicon of modifiers from a YAML file.

        Args:
            filepath: the .yaml file containing modifier rules

        Returns:
            context_rule: a list of ConTextRule objects
        Raises:
            KeyError: if the dictionary contains any keys other than
                those accepted by ConTextRule.__init__
        """

        import yaml
        import urllib.request, urllib.error, urllib.parse

        def _get_fileobj(_file):
            if not urllib.parse.urlparse(_file).scheme:
                _file = "file://" + _file
            return urllib.request.urlopen(_file, data=None)

        f0 = _get_fileobj(_file)
        context_rules = [
            ConTextRule.from_dict(data) for data in yaml.safe_load_all(f0)
        ]
        f0.close()
        return {"item_data": context_rules}

    @classmethod
    def from_json(cls, filepath):
        """Read in a lexicon of modifiers from a JSON file.

        Args:
            filepath: the .json file containing modifier rules

        Returns:
            context_item: a list of ConTextRule objects
        Raises:
            KeyError: if the dictionary contains any keys other than
                those accepted by ConTextRule.__init__
        """

        with open(filepath) as file:
            modifier_data = json.load(file)
        context_rules = []
        for data in modifier_data["context_rules"]:
            context_rules.append(ConTextRule.from_dict(data))
        return context_rules

    @classmethod
    def from_dict(cls, rule_dict):
        """Reads a dictionary into a ConTextRule. Used when reading from a json file.

        Args:
            item_dict: the dictionary to convert

        Returns:
            item: the ConTextRule created from the dictionary

        Raises:
            ValueError: if the json is invalid
        """
        keys = set(rule_dict.keys())
        invalid_keys = keys.difference(cls._ALLOWED_KEYS)
        if invalid_keys:
            msg = (
                "JSON object contains invalid keys: {0}.\n"
                "Must be one of: {1}".format(invalid_keys, cls._ALLOWED_KEYS)
            )
            raise ValueError(msg)
        rule = ConTextRule(**rule_dict)
        return rule

    @classmethod
    def to_json(cls, context_rules, filepath):
        """Writes ConTextItems to a json file.

        Args:
            item_data: a list of ConTextItems that will be written to a file.
            filepath: the .json file to contain modifier rules
        """

        data = {"context_rules": [rule.to_dict() for rule in context_rules]}
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)

    def to_dict(self):
        """Converts ConTextItems to a python dictionary. Used when writing context rules to a json file.

        Returns:
            rule_dict: the dictionary containing the ConTextRule info.
        """
        rule_dict = {}
        for key in self._ALLOWED_KEYS:
            rule_dict[key] = self.__dict__.get(key)
        return rule_dict

    def __repr__(self):
        return f"ConTextRule(literal='{self.literal}', category='{self.category}', pattern={self.pattern}, direction='{self.direction}')"
