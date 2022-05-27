from spacy.matcher import Matcher, PhraseMatcher
from .regex_matcher import RegexMatcher
from .base_rule import BaseRule

from spacy.tokens import Span


class MedspacyMatcher:
    """MedspacyMatcher is a class which combines spaCy's Matcher and PhraseMatcher classes
    along with medspaCy's RegexMatcher and acts as one single matcher using 3 different types of rules:
        - Exact phrases
        - List of dictionaries for matching on token attributes (see https://spacy.io/usage/rule-based-matching#matcher)
        - Regular expression matches. Note that regular-expression matching is not natively supported by spaCy and could
                result in unexpected matched spans if match boundaries do not align with token boundaries.
    Rules can be defined by any class which inherits from medspacy.common.BaseRule, such as:
        medspacy.target_matcher.TargetRule
        medspacy.context.ConTextRule
    """

    name = "medspacy_matcher"

    def __init__(self, nlp, phrase_matcher_attr="LOWER", prune=True):
        """Create a MedspacyMatcher.
        Params:
            nlp: A spaCy Language model.
            phrase_matcher_attr: The attribute to use for spaCy's PhraseMatcher (default is 'LOWER')
            prune: Whether or not to prune matches which overlap or are substrings of another match.
                For example, if "no history of" and "history of" are both matches, setting prune to True
                would drop "history of".
                Default True.
        """
        self.nlp = nlp
        self._rule_ids = set()
        self._rules = list()
        self.labels = set()
        self._rule_item_mapping = dict()
        self.prune = prune

        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr=phrase_matcher_attr)
        self.regex_matcher = RegexMatcher(self.nlp.vocab)

    @property
    def rules(self):
        return self._rules

    def add(self, rules):
        """Add a list of rules to the matcher. Rules must inherit from medspacy.common.BaseRule,
        such as medspacy.target_matcher.TargetRule or medspacy.context.ConTextRule."""
        i = len(self._rules)
        self._rules += rules

        for rule in rules:
            if not isinstance(rule, BaseRule):
                raise ValueError(
                    "Rules must inherit from medspacy.common.BaseRule, "
                    "such as medspacy.target_matcher.TargetRule."
                )
            self.labels.add(rule.category)
            rule_id = f"{rule.category}_{i}"
            rule._rule_id = rule_id
            self._rule_item_mapping[rule_id] = rule
            if rule.pattern is not None:
                # If it's a string, add a RegEx
                if isinstance(rule.pattern, str):
                    self.regex_matcher.add(rule_id, [rule.pattern], rule.on_match)
                # If it's a list, add a pattern dictionary
                elif isinstance(rule.pattern, list):
                    self.matcher.add(rule_id, [rule.pattern], on_match=rule.on_match)
                else:
                    raise ValueError(
                        "The pattern argument must be either a string or a list, not {0}".format(
                            type(rule.pattern)
                        )
                    )
            else:
                self.phrase_matcher.add(
                    rule_id, [self.nlp.make_doc(rule.literal.lower())], on_match=rule.on_match
                )
            i += 1

    def __call__(self, doc):
        """Call MedspacyMatcher on a doc and return a single list of matches. If self.prune is True,
        in the case of overlapping matches the longest will be returned."""
        matches = self.matcher(doc)
        matches += self.phrase_matcher(doc)
        matches += self.regex_matcher(doc)
        if self.prune:
            matches = prune_overlapping_matches(matches)
        return matches


def prune_overlapping_matches(matches, strategy="longest"):
    if strategy != "longest":
        raise NotImplementedError()

    # Make a copy and sort
    unpruned = sorted(matches, key=lambda x: (x[1], x[2]))
    pruned = []
    num_matches = len(matches)
    if num_matches == 0:
        return matches
    curr_match = unpruned.pop(0)

    while True:
        if len(unpruned) == 0:
            pruned.append(curr_match)
            break
        next_match = unpruned.pop(0)

        # Check if they overlap
        if overlaps(curr_match, next_match):
            # Choose the larger span
            longer_span = max(curr_match, next_match, key=lambda x: (x[2] - x[1]))
            pruned.append(longer_span)
            if len(unpruned) == 0:
                break
            curr_match = unpruned.pop(0)
        else:
            pruned.append(curr_match)
            curr_match = next_match
    # Recursive base point
    if len(pruned) == num_matches:
        return pruned
    # Recursive function call
    else:
        return prune_overlapping_matches(pruned)


def overlaps(a, b):
    if _match_overlaps(a, b) or _match_overlaps(b, a):
        return True
    return False


def _match_overlaps(a, b):
    _, a_start, a_end = a
    _, b_start, b_end = b
    if a_start >= b_start and a_start < b_end:
        return True
    if a_end > b_start and a_end <= b_end:
        return True
    return False


def matches_to_spans(doc, matches, set_label=True):
    spans = []
    for (rule_id, start, end) in matches:
        if set_label:
            label = doc.vocab.strings[rule_id]
        else:
            label = None
        spans.append(Span(doc, start=start, end=end, label=label))
    return spans
