from __future__ import annotations

from typing import Optional, List, Dict, Any

import srsly
from spacy.tokens import Span

from ..context import ConTextModifier
from ..util import tuple_overlaps


class ConTextGraph:
    """
    The ConTextGraph class defines the internal structure of the ConText algorithm. It stores a collection of modifiers,
    matched with ConTextRules, and targets from some other source such as the TargetMatcher or a spaCy NER model.

    Each modifier can have some number of associated targets that it modifies. This relationship is stored as edges of
    of the graph.
    """

    def __init__(
        self,
        targets: Optional[List[Span]] = None,
        modifiers: Optional[List[ConTextModifier]] = None,
        edges: Optional[List] = None,
        prune_on_modifier_overlap: bool = False,
        prune_modifier_overlap: bool = False,
    ):
        """
        Creates a new ConTextGraph object.

        Args:
            targets: A spans that context might modify.
            modifiers: A list of ConTextModifiers that might modify the targets.
            edges: A list of edges between targets and modifiers representing the modification relationship.
            prune_on_modifier_overlap: Whether to prune modifiers when one modifier completely covers another.
            prune_modifier_overlap: Whether to prune overlapping modifiers after they have been linked to
                targets, preferring modifiers which modified more targets. See `prune_overlapping_modifiers`.
        """
        self.targets = targets if targets is not None else []
        self.modifiers = modifiers if modifiers is not None else []
        self.edges = edges if edges is not None else []
        self.prune_on_modifier_overlap = prune_on_modifier_overlap
        self.prune_modifier_overlap = prune_modifier_overlap

    def update_scopes(self):
        """
        Update the scope of all ConTextModifier.

        For each modifier in a list of ConTextModifiers, check against each other
        modifier to see if one of the modifiers should update the other.
        This allows neighboring similar modifiers to extend each other's
        scope and allows "terminate" modifiers to end a modifier's scope.
        """
        for i in range(len(self.modifiers) - 1):
            modifier1 = self.modifiers[i]
            for j in range(i + 1, len(self.modifiers)):
                modifier2 = self.modifiers[j]
                # TODO: Add modifier -> modifier edges
                modifier1.limit_scope(modifier2)
                modifier2.limit_scope(modifier1)

    def apply_modifiers(self):
        """
        Checks each target/modifier pair. If modifier modifies target,
        create an edge between them.
        """
        if self.prune_on_modifier_overlap:
            for i in range(len(self.modifiers) - 1, -1, -1):
                modifier = self.modifiers[i]
                for target in self.targets:
                    if tuple_overlaps(
                        (target.start, target.end), modifier.modifier_span
                    ):
                        self.modifiers.pop(i)
                        break

        for target in self.targets:
            for modifier in self.modifiers:
                if modifier.modifies(target):
                    modifier.modify(target)

        # Now do a second pass and reduce the number of targets
        # for any modifiers with a max_targets int
        for modifier in self.modifiers:
            modifier.reduce_targets()

        # Prune overlapping modifiers only after linking so that a modifier
        # which did not modify any target cannot eliminate an overlapping
        # modifier which did. See https://github.com/medspacy/medspacy/issues/155.
        if self.prune_modifier_overlap:
            self.prune_overlapping_modifiers()

        edges = []
        for modifier in self.modifiers:
            for target in modifier._targets:
                edges.append((target, modifier))

        self.edges = edges

    def prune_overlapping_modifiers(self):
        """
        Prunes overlapping modifiers after they have been linked to targets.

        When two modifiers overlap, the modifier which modified fewer targets
        is dropped. This keeps a modifier that successfully modified a target
        over one that did not, for example keeping the FORWARD "no" (which
        negates the following entity) over the BACKWARD ": no" (which modifies
        nothing) in "FINDINGS: No pneumonia". PSEUDO and TERMINATE modifiers
        never modify targets directly -- their purpose is to cancel other
        modifiers -- so overlaps involving them are resolved by keeping the
        longest span, as before. When both modifiers modified the same number
        of targets, the longest modifier span is kept; remaining ties are
        broken by keeping the earliest span, matching the previous pruning
        behavior.
        """
        dropped = set()
        for i, modifier1 in enumerate(self.modifiers):
            if i in dropped:
                continue
            span1 = modifier1.modifier_span
            for j in range(i + 1, len(self.modifiers)):
                if j in dropped:
                    continue
                modifier2 = self.modifiers[j]
                span2 = modifier2.modifier_span
                if not tuple_overlaps(span1, span2):
                    continue
                if self._keep_first_modifier(
                    modifier1, span1, modifier2, span2
                ):
                    dropped.add(j)
                else:
                    dropped.add(i)
                    break
        self.modifiers = [
            modifier
            for i, modifier in enumerate(self.modifiers)
            if i not in dropped
        ]

    @staticmethod
    def _keep_first_modifier(
        modifier1: ConTextModifier,
        span1: tuple,
        modifier2: ConTextModifier,
        span2: tuple,
    ) -> bool:
        """
        Returns True if `modifier1` should be kept over the overlapping `modifier2`.
        """
        # PSEUDO and TERMINATE modifiers never modify targets themselves; they
        # exist to cancel other modifiers, so resolve these overlaps by span
        # length as before rather than by linked target count.
        if (
            modifier1.direction in ("PSEUDO", "TERMINATE")
            or modifier2.direction in ("PSEUDO", "TERMINATE")
        ):
            return ConTextGraph._keep_longer_span(span1, span2)
        num_targets1 = len(modifier1._targets)
        num_targets2 = len(modifier2._targets)
        if num_targets1 != num_targets2:
            return num_targets1 > num_targets2
        return ConTextGraph._keep_longer_span(span1, span2)

    @staticmethod
    def _keep_longer_span(span1: tuple, span2: tuple) -> bool:
        """Returns True if `span1` should be kept over `span2`: longest, then earliest."""
        len1 = span1[1] - span1[0]
        len2 = span2[1] - span2[0]
        if len1 != len2:
            return len1 > len2
        return span1[0] <= span2[0]

    def __repr__(self):
        return f"<ConTextGraph> with {len(self.targets)} targets and {len(self.modifiers)} modifiers"

    def serialized_representation(self) -> Dict[str, Any]:
        """
        Returns the serialized representation of the ConTextGraph
        """
        return self.__dict__

    @classmethod
    def from_serialized_representation(cls, serialized_representation) -> ConTextGraph:
        """
        Creates the ConTextGraph from the serialized representation
        """
        context_graph = ConTextGraph(**serialized_representation)

        return context_graph


@srsly.msgpack_encoders("context_graph")
def serialize_context_graph(obj, chain=None):
    if isinstance(obj, ConTextGraph):
        return {"context_graph": obj.serialized_representation()}
    return obj if chain is None else chain(obj)


@srsly.msgpack_decoders("context_graph")
def deserialize_context_graph(obj, chain=None):
    if "context_graph" in obj:
        return ConTextGraph.from_serialized_representation(obj["context_graph"])
    return obj if chain is None else chain(obj)
