class ConTextItem:

    def __init__(
        self,
        *args,
        **kwargs
    ):
        """
        Warning: Deprecated.
        ConTextItem has been replaced with ConTextRule:
            >>> from medspacy.context import ConTextRule
            >>> rule = ConTextRule("no evidence of", "NEGATED_EXISTENCE", direction="FORWARD")

        """
        raise NotImplementedError("ConTextItem has been deprecated and replaced with ConTextRule. "
                                  "Please import ConTextRule as: "
                                  "`from medspacy.context import ConTextRule`")