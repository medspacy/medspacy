from ..common.base_rule import BaseRule

class TargetRule(BaseRule):
    def __init__(self, literal, category, pattern=None, on_match=None, meta=None, attributes=None):
        """Class for defining rules for extracting entities from text using TargetMatcher.
        Params:
            literal (str): The actual string of a concept. If pattern is None,
                this string will be lower-cased and matched to the lower-case string.
                If `pattern` is not None, this argument will not be used for actual matching
                but can be used as a reference as the rule name.
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
            meta (dict or None): Optional dictionary of metadata.
            attributes (dict or None): Optional custom attribute names to set for a Span matched by the rule.
                These attribute names are stored under Span._.<attribute_name>.
                For example, if attributes={'is_historical':True}, then any spans matched by this rule
                will have span._.is_historical = True
        """
        super().__init__(literal, category, pattern, on_match, meta)
        self.attributes = attributes
        self._rule_id = None


        
    def __repr__(self):
        return f"""TargetRule(literal="{self.literal}", category="{self.category}", pattern={self.pattern}, attributes={self.attributes}, on_match={self.on_match})"""
