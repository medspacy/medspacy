from typing import Iterable, Callable, Any, Literal

from spacy.tokens import Span

from medspacy.postprocess import PostprocessingPattern


class PostprocessingRule:
    def __init__(
        self,
        patterns: Iterable[PostprocessingPattern],
        action: Callable,
        name: str = None,
        description: str = None,
        input_type: Literal["ents", "group"] = "ents",
        span_group_name: str = "medspacy_spans",
        **kwargs,
    ):
        """
        A PostprocessingRule checks conditions of a spaCy Span entity and executes some action if all rules are met.

        patterns: A list of PostprocessingPatterns, each of which check a condition of an entity.
        action: A function to call with the entity as an argument. This function should take the following arguments:
            ent: The spacy span
            i: The index of ent
            input_type: "ents" or "group". Describes where to look for spans.
            span_group_name: The name of the span group used when `input_type` is "group".
            kwargs: Any additional keyword arguments for action.
        name: Optional name of direction.
        description: Optional description of the direction.
        kwargs: Optional keyword arguments to send to `action`.

        """
        self.patterns = patterns
        self.action = action
        self.name = name
        self.description = description
        self.input_type = input_type
        self.span_group_name = span_group_name
        self.kwargs = kwargs

    def __call__(self, ent, i, debug=False):
        """
        Iterate through all the rules in self.rules.
        If any pattern does not pass (ie., return True), then returns False.
        If they all pass, execute self.action and return True.
        """
        for pattern in self.patterns:
            # If this is a tuple, at least one has to pass
            if isinstance(pattern, tuple):
                passed = False
                for subpattern in pattern:
                    rslt = subpattern(ent)
                    if rslt is True:
                        passed = True
                        break
                if passed is False:
                    return False
            # Otherwise just check a single value
            else:
                rslt = pattern(ent)
                if rslt is False:
                    return False

        # Every pattern passed - do the action
        if debug:
            print("Passed:", self, "on ent:", ent, ent.sent)

        try:
            if self.kwargs:
                self.action(
                    ent, i, self.input_type, self.span_group_name, **self.kwargs
                )
            else:
                self.action(ent, i)
        except TypeError:
            _raise_action_error(
                self.action,
                (ent, i, self.input_type, self.span_group_name, self.kwargs),
            )

    def __repr__(self):
        return f"PostprocessingRule: {self.name} - {self.description}"


def _raise_action_error(func, args):
    raise ValueError(
        f"The action function {func} does not have the correct number of arguments. "
        f"Any action function must start with two arguments: (ent, i) - the span and the index of "
        f"the span in doc.ents. Any additional arguments must be provided in a tuple "
        f"in `direction.action_args`. Actual arguments passed in: {args} "
    )
