from __future__ import annotations
import srsly
from medspacy.context.context_rule import ConTextRule
class ConTextModifier:
    """Represents a concept found by ConText in a document.
    Is the result of ConTextRule matching a span of text in a Doc.
    """

    def __init__(self, context_rule, start, end, doc, _scope_start=None, _scope_end=None, _use_context_window=False):
        """Create a new ConTextModifier from a document span.

        context_item (int): The ConTextRule object which defines the modifier.
        start (int): The start token index.
        end (int): The end token index (non-inclusive).
        doc (Doc): The spaCy Doc which contains this span.
        """
        self._context_rule = context_rule
        self.start = start
        self.end = end
        self.doc = doc

        self._targets = []
        self._num_targets = 0

        self._use_context_window = _use_context_window
        self._scope_start = _scope_start
        self._scope_end = _scope_end
        if self._scope_end is None or self._scope_start is None:
            self.set_scope()

    @property
    def span(self):
        """The spaCy Span object, which is a view of self.doc, covered by this match."""
        return self.doc[self.start : self.end]

    @property
    def rule(self):
        """Returns the associated direction."""
        return self._context_rule

    @property
    def direction(self):
        return self.rule.direction

    @property
    def category(self):
        """Returns the associated category."""
        return self.rule.category

    @property
    def scope(self):
        """Returns the associated scope."""
        return self.doc[self._scope_start : self._scope_end]

    @property
    def allowed_types(self):
        """Returns the associated allowed types."""
        return self.rule.allowed_types

    @property
    def excluded_types(self):
        """Returns the associated excluded types."""
        return self.rule.excluded_types

    @property
    def num_targets(self):
        """Returns the associated number of targets."""
        return self._num_targets

    @property
    def max_targets(self):
        """Returns the associated maximum number of targets."""
        return self.rule.max_targets

    @property
    def max_scope(self):
        """Returns the associated maximum scope."""
        return self.rule.max_scope

    def set_scope(self):
        """Applies the direction of the ConTextRule which generated
        this ConTextModifier to define a scope.
        If self.max_scope is None, then the default scope is the sentence which it occurs in
        in whichever direction defined by self.direction.
        For example, if the direction is "forward", the scope will be [self.end: sentence.end].
        If the direction is "backward", it will be [self.start: sentence.start].

        If self.max_scope is not None and the length of the default scope is longer than self.max_scope,
        it will be reduced to self.max_scope.


        """
        # If ConText is set to use defined windows, do that instead of sentence splitting
        if self._use_context_window:
            full_scope_span = self.span._.window(n=self.rule.max_scope)
            # # Up to the beginning of the doc
            # full_scope_start = max(
            #     (0, self.start - self.rule.max_scope)
            # )
            # # Up to the end of the doc
            # full_scope_end = min(
            #     (len(self.span.doc), self.end + self.rule.max_scope)
            # )
            # full_scope_span = self.span.doc[full_scope_start:full_scope_end]
        # Otherwise, use the sentence
        else:
            full_scope_span = self.doc[self.start].sent
            if full_scope_span is None:
                raise ValueError(
                    "ConText failed because sentence boundaries have not been set and 'use_context_window' is set to False. "
                    "Add an upstream component such as the dependency parser, Sentencizer, or PyRuSH to detect sentence "
                    "boundaries or initialize ConTextComponent with 'use_context_window=True.'"
                )

        if self.direction.lower() == "forward":
            self._scope_start, self._scope_end = self.end, full_scope_span.end
            if (
                self.max_scope is not None
                and (self._scope_end - self._scope_start) > self.max_scope
            ):
                self._scope_end = self.end + self.max_scope

        elif self.direction.lower() == "backward":
            self._scope_start, self._scope_end = (
                full_scope_span.start,
                self.start,
            )
            if (
                self.max_scope is not None
                and (self._scope_end - self._scope_start) > self.max_scope
            ):
                self._scope_start = self.start - self.max_scope
        else:  # bidirectional
            self._scope_start, self._scope_end = (
                full_scope_span.start,
                full_scope_span.end,
            )

            # Set the max scope on either side
            # Backwards
            if self.max_scope is not None and (self.start - self._scope_start) > self.max_scope:
                self._scope_start = self.start - self.max_scope
            # Forwards
            if self.max_scope is not None and (self._scope_end - self.end) > self.max_scope:
                self._scope_end = self.end + self.max_scope

    def update_scope(self, span):
        """Change the scope of self to be the given spaCy span.

        span (Span): a spaCy Span which contains the scope
        which a modifier should cover.
        """
        self._scope_start, self._scope_end = span.start, span.end

    def limit_scope(self, other):
        """If self and obj have the same category
        or if obj has a directionality of 'terminate',
        use the span of obj to update the scope of self.
        Limiting the scope of two modifiers of the same category
        reduces the number of modifiers. For example, in
        'no evidence of CHF, no pneumonia', 'pneumonia' will only
        be modified by 'no', not 'no evidence of'.
        'terminate' modifiers limit the scope of a modifier
        like 'no evidence of' in 'no evidence of CHF, **but** there is pneumonia'

        other (ConTextModifier)
        Returns True if obj modfified the scope of self
        """
        if self.span.sent != other.span.sent:
            return False
        if self.direction.upper() == "TERMINATE":
            return False
        # Check if the other modifier is a type which can modify self
        # or if they are the same category. If not, don't reduce scope.
        if (
            (other.direction.upper() != "TERMINATE")
            and (other.category.upper() not in self.rule.terminated_by)
            and (other.category.upper() != self.category.upper())
        ):
            return False

        # If two modifiers have the same category but modify different target types,
        # don't limit scope.
        if self.category == other.category and (
            (self.allowed_types != other.allowed_types)
            or (self.excluded_types != other.excluded_types)
        ):
            return False

        orig_scope = self.scope
        if self.direction.lower() in ("forward", "bidirectional"):
            if other > self:
                self._scope_end = min(self._scope_end, other.start)
        if self.direction.lower() in ("backward", "bidirectional"):
            if other < self:
                self._scope_start = max(self._scope_start, other.end)
        return orig_scope != self.scope

    def modifies(self, target):
        """Returns True if the target is within the modifier scope
        and self is allowed to modify target.

        target (Span): a spaCy span representing a target concept.
        """
        # If the target and modifier overlap, meaning at least one token
        # one extracted as both a target and modifier, return False
        # to avoid self-modifying concepts

        if self.overlaps_target(target):
            return False
        if self.direction in ("TERMINATE", "PSEUDO"):
            return False
        if not self.allows(target.label_.upper()):
            return False

        if target[0] in self.scope or target[-1] in self.scope:
            if not self.on_modifies(target):
                return False
            else:
                return True
        return False

    def allows(self, target_label):
        """Returns True if a modifier is able to modify a target type.
        A modifier may not be allowed if either self.allowed_types is not None and
        target_label is not in it, or if self.excluded_types is not None and
        target_label is in it.
        """
        if self.allowed_types is not None:
            if target_label not in self.allowed_types:
                return False
            return True
        if self.excluded_types is not None:
            if target_label not in self.excluded_types:
                return True
            return False
        return True

    def on_modifies(self, target):
        """If the ConTextRule used to define a ConTextModifier has an on_modifies callback function,
        evaluate and return either True or False.
        If on_modifies is None, return True.
        """
        if self.rule.on_modifies is None:
            return True
        # Find the span in between the target and modifier
        start = min(target.end, self.span.end)
        end = max(target.start, self.span.start)
        span_between = target.doc[start:end]
        rslt = self.rule.on_modifies(target, self.span, span_between)
        if rslt not in (True, False):
            raise ValueError(
                "The on_modifies function must return either True or False indicating "
                "whether a modify modifies a target. Actual value: {0}".format(rslt)
            )
        return rslt

    def modify(self, target):
        """Add target to the list of self._targets and increment self._num_targets."""
        self._targets.append(target)
        self._num_targets += 1

    def reduce_targets(self):
        """If self.max_targets is not None, reduce the targets which are modified
        so that only the n closest targets are left. Distance is measured as
        the distance to either the start or end of a target (whichever is closer).
        """
        if self.max_targets is None or self.num_targets <= self.max_targets:
            return

        target_dists = []
        for target in self._targets:
            dist = min(abs(self.start - target.end), abs(target.start - self.end))
            target_dists.append((target, dist))
        srtd_targets, _ = zip(*sorted(target_dists, key=lambda x: x[1]))
        self._targets = srtd_targets[: self.max_targets]
        self._num_targets = len(self._targets)

    def overlaps(self, other):
        """Returns whether the object overlaps with another span

        other (): the other object to check for overlaps

        RETURNS: true if there is overlap, false otherwise.
        """
        return (
            self.span[0] in other.span
            or self.span[-1] in other.span
            or other.span[0] in self.span
            or other.span[-1] in self.span
        )

    def overlaps_target(self, target):
        """Returns True if self overlaps with a spaCy span."""
        return (
            self.span[0] in target
            or self.span[-1] in target
            or target[0] in self.span
            or target[-1] in self.span
        )

    def __gt__(self, other):
        return self.span > other.span

    def __ge__(self, other):
        return self.span >= other.span

    def __lt__(self, other):
        return self.span < other.span

    def __le__(self, other):
        return self.span <= other.span

    def __len__(self):
        return len(self.span)

    def __repr__(self):
        return f"<ConTextModifier> [{self.start}, {self.end}, {self.category}]"

    def serialized_representation(self):
        """
        Serialized Representation of the modifier
        """

        KEYS_TO_KEEP = ["start", "end", "_use_context_window", "_scope_start", "_scope_end"]

        modifier_dict = self.__dict__

        rule_dict = modifier_dict["_context_rule"].to_dict()

        dict_repr = dict((key, modifier_dict[key]) for key in KEYS_TO_KEEP)
        dict_repr["context_rule"] = rule_dict

        return dict_repr

    @classmethod
    def from_serialized_representation(cls, serialized_representation) -> ConTextModifier:
        """
        Instantiates the class from the serialized representation
        """
        rule = ConTextRule.from_dict(serialized_representation["context_rule"])

        serialized_representation["context_rule"] = rule
        serialized_representation["doc"] = None #TODO: remove the dependency of ConTextModifier on Doc

        return ConTextModifier(**serialized_representation)


@srsly.msgpack_encoders("modifiers")
def serialize_modifiers(obj, chain=None):
    if isinstance(obj, list) and isinstance(obj[0], ConTextModifier):
        return {"modifiers": [modifier.serialized_representation() for modifier in obj]}
    return obj if chain is None else chain(obj)

@srsly.msgpack_encoders("modifier")
def serialize_modifier(obj, chain=None):
    if isinstance(obj, ConTextModifier):
        return obj.serialized_representation()
    return obj if chain is None else chain(obj)

@srsly.msgpack_decoders("modifiers")
def deserialize_modifiers(obj, chain=None):
    if "modifiers" in obj:
        obj["modifiers"] = [ConTextModifier.from_serialized_representation(serialized_modifier) for serialized_modifier in obj["modifiers"]]
        return obj
    return obj if chain is None else chain(obj)

@srsly.msgpack_decoders("modifier")
def deserialize_modifier(obj, chain=None):
    if "modifier" in obj:
        return ConTextModifier.from_serialized_representation(obj["modifier"])
    return obj if chain is None else chain(obj)