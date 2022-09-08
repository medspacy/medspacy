from __future__ import annotations
from typing import Optional, List, Dict, Any
import srsly


class ConTextGraph:
    def __init__(
        self,
        targets: Optional[List] = None,
        modifiers: Optional[List] = None,
        edges: Optional[List] = None,
        remove_overlapping_modifiers=False,
    ):
        self.targets = targets if targets is not None else []
        self.modifiers = modifiers if modifiers is not None else []
        self.edges = edges if edges is not None else []
        self.remove_overlapping_modifiers = remove_overlapping_modifiers

    def update_scopes(self):
        """Update the scope of all ConTextModifier.

        For each modifier in a list of ConTextModifiers, check against each other
        modifier to see if one of the modifiers should update the other.
        This allows neighboring similar modifiers to extend each other's
        scope and allows "terminate" modifiers to end a modifier's scope.

        Args:
            marked_modifiers: A list of ConTextModifiers in a Doc.
        """
        for i in range(len(self.modifiers) - 1):
            modifier1 = self.modifiers[i]
            for j in range(i + 1, len(self.modifiers)):
                modifier2 = self.modifiers[j]
                # TODO: Add modifier -> modifier edges
                modifier1.limit_scope(modifier2)
                modifier2.limit_scope(modifier1)

    def apply_modifiers(self):
        """Checks each target/modifier pair. If modifier modifies target,
        create an edge between them.

        Args:
            marked_targets: A list of Spans
            marked_modifiers: A list of ConTextModifiers

        RETURNS
            edges: A list of tuples consisting of target/modifier pairs
        """
        if self.remove_overlapping_modifiers:
            for i in range(len(self.modifiers) - 1, -1, -1):
                modifier = self.modifiers[i]
                for target in self.targets:
                    if overlap_target_modifiers(target, modifier.span):
                        self.modifiers.pop(i)
                        break

        edges = []
        for target in self.targets:
            for modifier in self.modifiers:
                if modifier.modifies(target):
                    modifier.modify(target)

        # Now do a second pass and reduce the number of targets
        # for any modifiers with a max_targets int
        for modifier in self.modifiers:
            modifier.reduce_targets()
            for target in modifier._targets:
                edges.append((target, modifier))

        self.edges = edges

    def __repr__(self):
        return "<ConTextGraph> with {0} targets and {1} modifiers".format(
            len(self.targets), len(self.modifiers)
        )

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


def overlap_target_modifiers(span1, span2):
    """Checks whether two modifiers overlap.

    Args:
        span1: the first span
        span2: the second span
    """
    return _spans_overlap(span1, span2)


def _spans_overlap(span1, span2):
    return (span1.end > span2.start and span1.end <= span2.end) or (
        span1.start >= span2.start and span1.start < span2.end
    )


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
