class BaseRule:

    def __init__(self, literal, category, pattern=None, on_match=None, metadata=None):
        """Base class for medspacy rules such as TargetRule and ConTextItem."""
        self.literal = literal
        self.category = category
        self.pattern = pattern
        self.on_match = on_match
        self.metadata = metadata