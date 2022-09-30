from typing import Union, Iterable

from spacy.tokens import Doc

from medspacy.preprocess import PreprocessingRule


class Preprocessor:
    """
    This is the medspacy Preprocessor class. It is designed as a wrapper for destructive preprocessing rules such as
    stripping or replacing text in a document before the text enters a spaCy pipeline.

    This is NOT a spaCy component and cannot be added to a spaCy pipeline. Please use the preprocessor before
    calling `nlp("your text here")`. SpaCy only allows for non-destructive processing on the text, but that is not
    always advisable for every project, so this enables destructive preprocessing when required.
    """
    def __init__(self, tokenizer):
        """

        Args:
            tokenizer:
        """
        self.tokenizer = tokenizer
        self._rules = []

    def add(self, rules: Union[PreprocessingRule, Iterable[PreprocessingRule]]):
        """
        Adds a PreprocessingRule or collection of PreprocessingRules to the Preprocessor.

        Args:
            rules: A single PreprocessingRule or a collection of PreprocessingRules to add.
        """
        if isinstance(rules, PreprocessingRule):
            rules = [rules]
        for rule in rules:
            if not isinstance(rule, PreprocessingRule):
                raise TypeError(f"Each rule must be an instance of PreprocessingRule, not {type(rule)}.")
        self._rules += rules

    def __call__(self, text, tokenize = True) -> Union[str, Doc]:
        """

        Args:
            text:
            tokenize:

        Returns:

        """
        for rule in self._rules:
            text = rule(text)

        if not tokenize:
            return text

        return self.tokenizer(text)
