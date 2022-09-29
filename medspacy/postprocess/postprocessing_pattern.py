from typing import Callable, Any

from spacy.tokens import Span


class PostprocessingPattern:
    """
    PostprocessingPatterns are callable functions and equality values wrapped together that will create triggers
    in the later Postprocessor as part of PostprocessingRules.
    """

    def __init__(self, condition: Callable, success_value: Any, **kwargs):
        """
        A PostprocessingPattern defines a single condition to check against an entity.

        Args:
            condition: A function to call on an entity. If the result of the function call equals success_value, then
                the pattern passes.
            success_value: The value which should be returned by condition(ent) in order for the pattern to pass. Must
                have == defined for condition(ent) == success_value.
            kwargs: Optional keyword arguments to call with condition(ent, **kwargs).
        """
        self.condition = condition
        self.success_value = success_value
        self.kwargs = kwargs

    def __call__(self, ent: Span) -> bool:
        """
        Call the PostprocessingPattern on the span specified.

        Args:
            ent: the span to process.

        Returns:
            Whether calling `condition` on the entity specified is `success_value`.
        """
        if self.kwargs:
            result = self.condition(ent, **self.kwargs)
        else:
            result = self.condition(ent)
        return result == self.success_value
