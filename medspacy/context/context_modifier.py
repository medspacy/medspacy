from __future__ import annotations

from typing import Optional, Tuple, Set, Union

from spacy.tokens import Doc, Span

from medspacy.context.context_rule import ConTextRule
from medspacy.util import tuple_overlaps
import srsly


class ConTextModifier:
    """
    Represents a concept found by ConText in a document. An instance of this class is the result of ConTextRule matching
    text in a Doc.
    """

    def __init__(
        self,
        context_rule: ConTextRule,
        start: int,
        end: int,
        doc: Doc,
        scope_start: Optional[int] = None,
        scope_end: Optional[int] = None,
        max_scope: Optional[int] = None,
    ):
        """
        Create a new ConTextModifier from a document span. Each modifier represents a span in the text and a surrounding
        window. Spans such as entities or other members of span groups that occur within this window can be modified by
        this ConTextModifier.

        Args:
            context_rule: The ConTextRule object which defines the modifier.
            start: The start token index.
            end: The end token index (non-inclusive).
            doc: The spaCy Doc which contains this span. This is needed to initialize the modifier but is not
                maintained.
            scope_start: The start token index of the scope.
            scope_end: The end index of the scope.
            max_scope: Whether to use scope values rather than sentence boundaries for modifications.
        """
        self._context_rule = context_rule
        self._start = start
        self._end = end

        self._targets = []
        self._num_targets = 0

        self._max_scope = max_scope
        self._scope_start = scope_start
        self._scope_end = scope_end
        if doc is not None and (self._scope_end is None or self._scope_start is None):
            self.__set_scope(doc)

    @property
    def modifier_span(self) -> Tuple[int, int]:
        """
        The spaCy Span object, which is a view of self.doc, covered by this match.
        """
        return self._start, self._end

    @property
    def rule(self) -> ConTextRule:
        """
        Returns the associated context rule.
        """
        return self._context_rule

    @property
    def direction(self) -> str:
        """
        Returns the associated direction.
        """
        return self.rule.direction

    @property
    def category(self) -> str:
        """
        Returns the associated category.
        """
        return self.rule.category

    @property
    def scope_span(self) -> Tuple[int, int]:
        """
        Returns the associated scope.
        """
        return self._scope_start, self._scope_end

    @property
    def allowed_types(self) -> Set[str]:
        """
        Returns the associated allowed types.
        """
        return self.rule.allowed_types

    @property
    def excluded_types(self) -> Set[str]:
        """
        Returns the associated excluded types.
        """
        return self.rule.excluded_types

    @property
    def num_targets(self) -> int:
        """
        Returns the associated number of targets.
        """
        return self._num_targets

    @property
    def max_targets(self) -> Union[int, None]:
        """
        Returns the associated maximum number of targets.
        """
        return self.rule.max_targets

    @property
    def max_scope(self) -> Union[int, None]:
        """
        Returns the associated maximum scope.
        """
        return self.rule.max_scope

    def __set_scope(self, doc: Doc):
        """
        Applies the direction of the ConTextRule which generated this ConTextModifier to define a scope. If
        self._max_scope is None, then the default scope is the sentence which it occurs in whichever direction defined by
        self.direction. For example, if the direction is "forward", the scope will be [self.end: sentence.end]. If the
        direction is "backward", it will be [self.start: sentence.start].

        If self.max_scope is not None and the length of the default scope is longer than self.max_scope, it will be
        reduced to self.max_scope.

        Args:
            doc: The spaCy doc to use to set scope.
        """
        # If ConText is set to use defined windows, do that instead of sentence splitting
        if self._max_scope:
            full_scope_span = doc[self._start : self._end]._.window(
                n=self.rule.max_scope
            )
        # Otherwise, use the sentence
        else:
            full_scope_span = doc[self._start].sent
            if full_scope_span is None:
                raise ValueError(
                    "ConText failed because sentence boundaries have not been set. Add an upstream component such as the "
                    "dependency parser, Sentencizer, or PyRuSH to detect sentence boundaries or initialize ConText with "
                    "`max_scope` set to a value greater than 0."
                )

        if self.direction.lower() == "forward":
            self._scope_start, self._scope_end = self._end, full_scope_span.end
            if (
                self.max_scope is not None
                and (self._scope_end - self._scope_start) > self.max_scope
            ):
                self._scope_end = self._end + self.max_scope

        elif self.direction.lower() == "backward":
            self._scope_start, self._scope_end = (
                full_scope_span.start,
                self._start,
            )
            if (
                self.max_scope is not None
                and (self._scope_end - self._scope_start) > self.max_scope
            ):
                self._scope_start = self._start - self.max_scope
        else:  # bidirectional
            self._scope_start, self._scope_end = (
                full_scope_span.start,
                full_scope_span.end,
            )

            # Set the max scope on either side
            # Backwards
            if (
                self.max_scope is not None
                and (self._start - self._scope_start) > self.max_scope
            ):
                self._scope_start = self._start - self.max_scope
            # Forwards
            if (
                self.max_scope is not None
                and (self._scope_end - self._end) > self.max_scope
            ):
                self._scope_end = self._end + self.max_scope

    def update_scope(self, span: Span):
        """
        Changes the scope of self to be the given spaCy span.

        Args:
            span: a spaCy Span which contains the scope which a modifier should cover.
        """
        self._scope_start = span.start
        self._scope_end = span.end

    def limit_scope(self, other: ConTextModifier) -> bool:
        """
        If self and other have the same category or if other has a directionality of 'terminate', use the span of other
        to update the scope of self. Limiting the scope of two modifiers of the same category reduces the number of
        modifiers. For example, in 'no evidence of CHF, no pneumonia', 'pneumonia' will only be modified by 'no', not
        'no evidence of'. 'terminate' modifiers limit the scope of a modifier like 'no evidence of' in 'no evidence of
        CHF, but there is pneumonia'

        Args:
            other: The modifier to check against.

        Returns:
            Whether the other modifier modified the scope of self.
        """
        if not tuple_overlaps(self.scope_span, other.scope_span):
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

        orig_scope = self.scope_span
        if self.direction.lower() in ("forward", "bidirectional"):
            if other > self:
                self._scope_end = min(self._scope_end, other.modifier_span[0])
        if self.direction.lower() in ("backward", "bidirectional"):
            if other < self:
                self._scope_start = max(self._scope_start, other.modifier_span[1])
        return orig_scope != self.scope_span

    def modifies(self, target: Span) -> bool:
        """
        Checks whether the target is within the modifier scope and if self is allowed to modify target.

        Args:
            target: a spaCy span representing a target concept.

        Returns:
            Whether the target is within `modifier_scope` and if self is allowed to modify the target.
        """
        # If the target and modifier overlap, meaning at least one token
        # one extracted as both a target and modifier, return False
        # to avoid self-modifying concepts

        if tuple_overlaps(
            self.modifier_span, (target.start, target.end)
        ):  # self.overlaps(target):
            return False
        if self.direction in ("TERMINATE", "PSEUDO"):
            return False
        if not self.allows(target.label_.upper()):
            return False

        if tuple_overlaps(self.scope_span, (target.start, target.end)):
            if not self.on_modifies(target):
                return False
            else:
                return True
        return False

    def allows(self, target_label: str) -> bool:
        """
        Returns whether if a modifier is able to modify a target type.

        Args:
            target_label: The target type to check.

        Returns:
            Whether the modifier is allowed to modify a target of the specified type. True if `target_label` in
            `self.allowed_types` or if `target_label` not in `self.excluded_tupes`. False otherwise.
        """
        if self.allowed_types is not None:
            return target_label in self.allowed_types
        if self.excluded_types is not None:
            return target_label not in self.excluded_types
        return True

    def on_modifies(self, target: Span) -> bool:
        """
        If the ConTextRule used to define a ConTextModifier has an `on_modifies` callback function, evaluate and return
        either True or False.

        Args:
            target: The spaCy span to evaluate.

        Returns:
            The result of the `on_modifies` callback for the rule. True if the callback is None.
        """
        if self.rule.on_modifies is None:
            return True
        # Find the span in between the target and modifier
        start = min(target.end, self._end)
        end = max(target.start, self._end)
        span_between = target.doc[start:end]
        rslt = self.rule.on_modifies(
            target, target.doc[self._start : self._end], span_between
        )
        if rslt not in (True, False):
            raise ValueError(
                "The on_modifies function must return either True or False indicating "
                "whether a modify modifies a target. Actual value: {0}".format(rslt)
            )
        return rslt

    def modify(self, target: Span):
        """
        Add target to the list of self._targets and increment self._num_targets.

        Args:
            target: The spaCy span to add.
        """
        self._targets.append(target)
        self._num_targets += 1

    def reduce_targets(self):
        """
        Reduces the number of targets to the n-closest targets based on the value of `self.max_targets`. If
        `self.max_targets` is None, no pruning is done.
        """
        if self.max_targets is None or self.num_targets <= self.max_targets:
            return

        target_dists = []
        for target in self._targets:
            dist = min(abs(self._start - target.end), abs(target.start - self._end))
            target_dists.append((target, dist))
        srtd_targets, _ = zip(*sorted(target_dists, key=lambda x: x[1]))
        self._targets = srtd_targets[: self.max_targets]
        self._num_targets = len(self._targets)

    def __gt__(self, other: ConTextModifier):
        return self._start > other.modifier_span[0]

    def __ge__(self, other):
        return self._start >= other.modifier_span[0]

    def __lt__(self, other):
        return self._end < other.modifier_span[1]

    def __le__(self, other):
        return self._end <= other.modifier_span[1]

    def __len__(self):
        return self._end - self._start

    def __repr__(self):
        return f"<ConTextModifier> [{self._start}, {self._end}, {self.category}]"

    def serialized_representation(self):
        """
        Serialized Representation of the modifier
        """
        dict_repr = dict()
        dict_repr["context_rule"] = self.rule.to_dict()
        dict_repr["start"] = self._start
        dict_repr["end"] = self._end
        dict_repr["max_scope"] = self._max_scope
        dict_repr["scope_start"] = self._scope_start
        dict_repr["scope_end"] = self._scope_end

        return dict_repr

    @classmethod
    def from_serialized_representation(
        cls, serialized_representation
    ) -> ConTextModifier:
        """
        Instantiates the class from the serialized representation
        """
        rule = ConTextRule.from_dict(serialized_representation["context_rule"])

        serialized_representation["context_rule"] = rule
        serialized_representation["doc"] = None

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
        obj["modifiers"] = [
            ConTextModifier.from_serialized_representation(serialized_modifier)
            for serialized_modifier in obj["modifiers"]
        ]
        return obj
    return obj if chain is None else chain(obj)


@srsly.msgpack_decoders("modifier")
def deserialize_modifier(obj, chain=None):
    if "modifier" in obj:
        return ConTextModifier.from_serialized_representation(obj["modifier"])
    return obj if chain is None else chain(obj)
