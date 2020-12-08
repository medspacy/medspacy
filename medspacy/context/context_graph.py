class ConTextGraph:
    def __init__(self, remove_overlapping_modifiers=False):
        self.targets = []
        self.modifiers = []
        self.edges = []
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

    def prune_modifiers(self):
        """Prune overlapping modifiers so that only the longest span is kept.

        For example, if "no" and "no evidence of" are both tagged as modifiers,
        only "no evidence of" will be kept.

        Additionally, this removes any modifiers which overlap with a target.
        For example, if doc.ents contains a span "does not know" and "not" is tagged by
        context as a modifier, "not" will be removed.

        # TODO: Consider only removing modifiers which are subspans.
        """

        unpruned = sorted(self.modifiers, key=lambda x: (x.end - x.end))
        if len(unpruned) > 0:
            rslt = self.prune_overlapping_modifiers(unpruned)
            self.modifiers = rslt

    def prune_overlapping_modifiers(self, modifiers):
        # Don't prune a single modifier
        if len(modifiers) == 1:
            return modifiers

        # Make a copy
        unpruned = list(modifiers)
        pruned = []
        num_mods = len(unpruned)
        curr_mod = unpruned.pop(0)

        while True:
            if len(unpruned) == 0:
                pruned.append(curr_mod)
                break
            # if len(unpruned) == 1:
            #     pruned.append(unpruned.pop(0))
            #     break
            next_mod = unpruned.pop(0)

            # Check if they overlap
            if curr_mod.overlaps(next_mod):
                # Choose the larger
                longer_span = max(curr_mod, next_mod, key=lambda x: (x.end - x.start))

                pruned.append(longer_span)
                if len(unpruned) == 0:
                    break
                curr_mod = unpruned.pop(0)
            else:
                pruned.append(curr_mod)
                curr_mod = next_mod
        # Recursion base point
        if len(pruned) == num_mods:
            return pruned
        return self.prune_overlapping_modifiers(pruned)

    def __repr__(self):
        return "<ConTextGraph> with {0} targets and {1} modifiers".format(
            len(self.targets), len(self.modifiers)
        )


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
