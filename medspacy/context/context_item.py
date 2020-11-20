import json


class ConTextItem:
    """An ConTextItem defines a ConText modifier. ConTextItems are rules define
    which spans are extracted as modifiers and how they behave, such as the phrase to be matched,
    the category/semantic class, the direction of the modifier in the text, and what types of target
    spans can be modfified.
    """

    _ALLOWED_RULES = (
        "FORWARD",
        "BACKWARD",
        "BIDIRECTIONAL",
        "TERMINATE",
        "PSEUDO",
    )
    _ALLOWED_KEYS = {
        "literal",
        "rule",
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
        rule="BIDIRECTIONAL",
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
    ):
        """Create an ConTextItem object.
        The primary arguments of `literal` `category`, and `rule` define
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
            category (str): The semantic class of the item.
            pattern (str, list or None): A spaCy pattern to match using token attributes.
                See https://spacy.io/usage/rule-based-matching.
            rule (str): The directionality or action of a modifier. This defines which part
                of a sentence a modifier will include as its scope. Entities within
                the scope will be considered to be modified.
                Valid values are:
                 - "FORWARD": Scope will begin after the end of a modifier and move
                    to the right towards the end of the sentence
                - "BACKWARD": Scope will begin before the beginning of a modifier
                    and move to the left towards the beginning of a sentence
                - "BIDIRECTIONAL": Scope will expand on either side of a modifier
                - "TERMINATE": A special rule to limit any other modifiers
                    if this phrase is in its scope.
                    Example: "no evidence of chf but there is pneumonia":
                        "but" will prevent "no evidence of" from modifying "pneumonia"
                - "PSEUDO": A special rule which will not modify any targets.
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
                If None, the scope will include the entire sentence in the direction of `rule`
                (ie., starting at the beginning of the sentence for "BACKWARD", end of the sentence for "FORWARD",
                and the entire sentence for "BIDIRECTIONAL".
                This is useful for requiring modifiers be very close to a concept in the text
                or for preventing too far of modifier ranges caused by undersplitting of sentences.
                Example: In the sentence "pt with chf, pna vs. rsv", "vs." will modify
                    only "pna" and "rsv" if max_scope=1 and rule="BIDIRECTIONAL".
            max_targets (int or None): The maximum number of targets which a modifier can modify.
                If None, will modify all targets in its scope.
            terminated_by (iterable or None): An optional array of other modifier categories which will
                terminate the scope of this modifier. If None, only "TERMINATE" will do this.
                Example: if a ConTextItem defining "positive for" has terminated_by={"NEGATED_EXISTENCE"},
                then in the sentence "positive for flu, negative for RSV", the positive modifier
                will modify "flu" but will be terminated by "negative for" and will not modify "RSV".
                This helps prevent multiple conflicting modifiers from distributing too far across
                a sentence.
            metadata (dict or None): A dict of additional data to pass in,
                such as free-text comments, additional attributes, or ICD-10 codes.
                Default None.

        Returns:
            item: a ConTextItem
        """
        self.literal = literal.lower()
        self.category = category.upper()
        self.pattern = pattern
        self.rule = rule.upper()
        self.on_match = on_match
        self.on_modifies = on_modifies

        if allowed_types is not None and excluded_types is not None:
            raise ValueError(
                "A ConTextItem was instantiated with non-null values for both allowed_types and excluded_types. "
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

        if self.rule not in self._ALLOWED_RULES:
            raise ValueError(
                "Rule {0} not recognized. Must be one of: {1}".format(
                    self.rule, self._ALLOWED_RULES
                )
            )

    @classmethod
    def from_yaml(cls, _file):
        """Read in a lexicon of modifiers from a YAML file.

        Args:
            filepath: the .yaml file containing modifier rules

        Returns:
            context_item: a list of ConTextItem objects
        Raises:
            KeyError: if the dictionary contains any keys other than
                those accepted by ConTextItem.__init__
        """

        import yaml
        import urllib.request, urllib.error, urllib.parse

        def _get_fileobj(_file):
            if not urllib.parse.urlparse(_file).scheme:
                _file = "file://" + _file
            return urllib.request.urlopen(_file, data=None)

        f0 = _get_fileobj(_file)
        context_items = [
            ConTextItem.from_dict(data) for data in yaml.safe_load_all(f0)
        ]
        f0.close()
        return {"item_data": context_items}

    @classmethod
    def from_json(cls, filepath):
        """Read in a lexicon of modifiers from a JSON file.

        Args:
            filepath: the .json file containing modifier rules

        Returns:
            context_item: a list of ConTextItem objects
        Raises:
            KeyError: if the dictionary contains any keys other than
                those accepted by ConTextItem.__init__
        """

        with open(filepath) as file:
            modifier_data = json.load(file)
        item_data = []
        for data in modifier_data["item_data"]:
            item_data.append(ConTextItem.from_dict(data))
        return item_data

    @classmethod
    def from_dict(cls, item_dict):
        """Reads a dictionary into a ConTextItem. Used when reading from a json file.

        Args:
            item_dict: the dictionary to convert

        Returns:
            item: the ConTextItem created from the dictionary

        Raises:
            ValueError: if the json is invalid
        """
        try:
            item = ConTextItem(**item_dict)
        except Exception as err:
            print(err)
            keys = set(item_dict.keys())
            invalid_keys = keys.difference(cls._ALLOWED_KEYS)
            msg = (
                "JSON object contains invalid keys: {0}.\n"
                "Must be one of: {1}".format(invalid_keys, cls._ALLOWED_KEYS)
            )
            raise ValueError(msg)

        return item

    @classmethod
    def to_json(cls, item_data, filepath):
        """Writes ConTextItems to a json file.

        Args:
            item_data: a list of ConTextItems that will be written to a file.
            filepath: the .json file to contain modifier rules
        """

        data = {"item_data": [item.to_dict() for item in item_data]}
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)

    def to_dict(self):
        """Converts ConTextItems to a python dictionary. Used when writing context items to a json file.

        Returns:
            item_dict: the dictionary containing the ConTextItem info.
        """
        item_dict = {}
        for key in self._ALLOWED_KEYS:
            item_dict[key] = self.__dict__.get(key)
        return item_dict

    def __repr__(self):
        return f"ConTextItem(literal='{self.literal}', category='{self.category}', pattern={self.pattern}, rule='{self.rule}')"
