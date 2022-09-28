"""The ConTextComponent definiton."""
from os import path

# Filepath to default rules which are included in package
from pathlib import Path
from typing import Iterable, Union, Optional, Dict, Any, Set, Literal

from spacy.tokens import Doc, Span
from spacy.language import Language

from .context_modifier import ConTextModifier
from .context_graph import ConTextGraph
from .context_rule import ConTextRule

from ..common.medspacy_matcher import MedspacyMatcher

#
DEFAULT_ATTRIBUTES = {
    "NEGATED_EXISTENCE": {"is_negated": True},
    "POSSIBLE_EXISTENCE": {"is_uncertain": True},
    "HISTORICAL": {"is_historical": True},
    "HYPOTHETICAL": {"is_hypothetical": True},
    "FAMILY": {"is_family": True},
}

DEFAULT_RULES_FILEPATH = path.join(
    Path(__file__).resolve().parents[2], "resources", "context_rules.json"
)


@Language.factory("medspacy_context")
class ConTextComponent:
    """
    The ConTextComponent for spaCy processing.

    This component matches modifiers in a Doc, defines their scope, and identifies edges between targets and modifiers.
    Sets two spaCy extensions:
            - Span._.modifiers: a list of ConTextModifier objects which modify a target Span
            - Doc._.context_graph: a ConText graph object which contains the targets,
                modifiers, and edges between them.
    """

    def __init__(
        self,
        nlp: Language,
        name: str = "medspacy_context",
        rules: Union[Iterable[ConTextRule], Literal["default"], None] = "default",
        phrase_matcher_attr: str = "LOWER",
        allowed_types: Optional[Set[str]] = None,
        excluded_types: Optional[Set[str]] = None,
        terminating_types: Optional[Dict[str, Iterable[str]]] = None,
        max_scope: Optional[int] = None,
        max_targets: Optional[int] = None,
        prune_on_modifier_overlap: bool = True,
        prune_on_target_overlap: bool = False,
        span_attrs: Union[
            Literal["default"], Dict[str, Dict[str, Any]], None
        ] = "default",
        input_span_type: Union[Literal["ents", "group"]] = "ents",
        span_group_name: str = "medspacy_spans",
    ):
        """
        Creates a new ConTextComponent.

        Args:
            nlp: A SpaCy Language object.
            name: The name of the component.
            rules: The rules to load. Default is "default", loads rules packaged with medspaCy that are derived from
                original ConText rules and years of practical applications at the US Department of Veterans Affairs.  If
                None, no rules are loaded. Otherwise, must be a list of ConTextRule objects.
            phrase_matcher_attr: The token attribute to use for PhraseMatcher for rules where `pattern` is None. Default
                is 'LOWER'.
            allowed_types: A global list of types included by context. Rules will operate on only spans with these
                labels.
            excluded_types: A global list of types excluded by context. Rules will not operate on spans with these
                labels.
            terminating_types: A global map of types to the types that can terminate them. This can be used to apply
                terminations to all rules of a particular type rather than adding to every rule individually in the
                ContextRule object.
            max_scope: The number of tokens around a modifier in a target can be modified. Default value is None,
                Context will use the sentence boundaries. If a value greater than zero, applies the window globally.
                Both options will be overridden by a more specific value in a ContextRule.
            max_targets: The maximum number of targets a modifier can modify. Default value is None, context will modify
                all targets in its scope. If a value greater than zero, applies this value globally. Both options will
                be overridden by a more specific value in a ContextRule.
            prune_on_modifier_overlap: Whether to prune modifiers which are substrings of another modifier. If True,
                will drop substrings completely. For example, if "no history of"  and "history of" are both
                ConTextRules,both will match the text "no history of afib", but only "no  history of" should modify
                afib. Default True.
            prune_on_target_overlap: Whether to remove any matched modifiers which overlap with target entities. If
                False, any overlapping modifiers will not modify the overlapping entity but will still modify any other
                targets in its scope. Default False.
            span_attrs: The optional span attributes to modify. Default option "default" uses attributes in
                `DEFAULT_ATTRIBUTES`. If a dictionary, format is mapping context modifier categories to a dictionary
                containing the attribute name and the value to set the attribute to when a  span is modified by a
                modifier of that category. If None, no attributes will be modified.
            input_span_type: "ents" or "group". Where to look for targets. "ents" will modify attributes of spans
                in doc.ents. "group" will modify attributes of spans in the span group specified by `span_group_name`.
            span_group_name: The name of the span group used when `input_span_type` is "group". Default is
                "medspacy_spans".
        """
        self.nlp = nlp
        self.name = name
        self.prune_on_modifier_overlap = prune_on_modifier_overlap
        self.prune_on_target_overlap = prune_on_target_overlap
        self.input_span_type = input_span_type
        self.span_group_name = span_group_name
        self.context_attributes_mapping = None

        self._i = 0
        self._categories = set()

        self.__matcher = MedspacyMatcher(
            nlp,
            phrase_matcher_attr=phrase_matcher_attr,
            prune=prune_on_modifier_overlap,
        )

        if span_attrs == "default":
            self.context_attributes_mapping = DEFAULT_ATTRIBUTES
            self.register_default_attributes()
        elif span_attrs:
            for _, attr_dict in span_attrs.items():
                for attr_name in attr_dict.keys():
                    if not Span.has_extension(attr_name):
                        raise ValueError(
                            f"Custom extension {attr_name} has not been set. Please ensure Span.set_extension is "
                            f"called for your pipeline's custom extensions."
                        )
            self.context_attributes_mapping = span_attrs

        self.register_graph_attributes()

        if max_scope is not None:
            if not (isinstance(max_scope, int) and max_scope > 0):
                raise ValueError(
                    f"If 'max_scope' is not None, must be a value greater than 0, not the current value: {max_scope}"
                )
        self.max_scope = max_scope

        self.allowed_types = allowed_types
        self.excluded_types = excluded_types
        self.max_targets = max_targets

        self.terminating_types = dict()
        if terminating_types:
            self.terminating_types = {
                k.upper(): v for (k, v) in terminating_types.items()
            }

        if rules and rules == "default":
            self.add(ConTextRule.from_json(DEFAULT_RULES_FILEPATH))
        elif rules:
            self.add(rules)

    @property
    def rules(self):
        """Returns list of ConTextItems"""
        return self.__matcher.rules

    @property
    def categories(self):
        """Returns list of categories from ConTextItems"""
        return self._categories

    def add(self, rules):
        """
        Adds a list of ConTextRule rules to ConText.

        Args:
            rules: a list of ConTextItems to add.
        """
        if isinstance(rules, ConTextRule):
            rules = [rules]
        for rule in rules:
            if not isinstance(rule, ConTextRule):
                raise TypeError("rules must be a list of ConTextRules.")
            self._categories.add(rule.category)

            # If global attributes like allowed_types and max_scope are defined,
            # check if the ConTextRule has them defined. If not, set to the global
            for attr in (
                "allowed_types",
                "excluded_types",
                "max_scope",
                "max_targets",
            ):
                value = getattr(self, attr)
                if value is None:  # No global value set
                    continue
                if (
                    getattr(rule, attr) is None
                ):  # If the direction itself has it defined, don't override
                    setattr(rule, attr, value)

            # Check custom termination points
            if rule.category.upper() in self.terminating_types:
                for other_modifier in self.terminating_types[rule.category.upper()]:
                    rule.terminated_by.add(other_modifier.upper())

        self.__matcher.add(rules)

    @classmethod
    def register_graph_attributes(cls):
        """
        Registers spaCy container custom attribute extensions.

        By default, will register Span._.modifiers and Doc._.context_graph.

        If self.add_attrs is True, will add additional attributes to span
            as defined in DEFAULT_ATTRS:
            - is_negated
            - is_historical
            - is_experiencer
        """
        Span.set_extension("modifiers", default=(), force=True)
        Doc.set_extension("context_graph", default=None, force=True)

    @classmethod
    def register_default_attributes(cls):
        """
        Registers the default values for the Span attributes defined in `DEFAULT_ATTRIBUTES`.
        """
        for attr_name in [
            "is_negated",
            "is_uncertain",
            "is_historical",
            "is_hypothetical",
            "is_family",
        ]:
            try:
                Span.set_extension(attr_name, default=False)
            except ValueError:  # Extension already set
                pass

    def set_context_attributes(self, edges):
        """
        Adds Span-level attributes to targets with modifiers.

        Args:
            edges: The edges of the ContextGraph to modify.

        """

        for (target, modifier) in edges:
            if modifier.category in self.context_attributes_mapping:
                attr_dict = self.context_attributes_mapping[modifier.category]
                for attr_name, attr_value in attr_dict.items():
                    setattr(target._, attr_name, attr_value)

    def __call__(self, doc, targets: str = None):
        """Applies the ConText algorithm to a Doc.

        Args:
            doc: a spaCy Doc
            targets: the custom attribute extension on doc to run over. Must contain an iterable of Span objects

        Returns:
            doc: a spaCy Doc
        """
        if not targets and self.input_span_type == "ents":
            targets = doc.ents
        elif not targets and self.input_span_type == "group":
            targets = doc.spans[self.span_group_name]
        elif targets:
            targets = getattr(doc._, targets)
        # Store data in ConTextGraph object
        # TODO: move some of this over to ConTextGraph
        context_graph = ConTextGraph(
            remove_overlapping_modifiers=self.prune_on_target_overlap
        )

        context_graph.targets = targets

        context_graph.modifiers = []
        matches = self.__matcher(doc)

        for (match_id, start, end) in matches:
            # Get the ConTextRule object defining this modifier
            rule = self.__matcher.rule_map[self.nlp.vocab[match_id].text]
            modifier = ConTextModifier(
                rule, start, end, doc, self.max_scope if self.max_scope else False
            )
            context_graph.modifiers.append(modifier)

        context_graph.update_scopes()
        context_graph.apply_modifiers()

        # Link targets to their modifiers
        for target, modifier in context_graph.edges:
            target._.modifiers += (modifier,)

        # If attributes need to be modified
        if self.context_attributes_mapping:
            self.set_context_attributes(context_graph.edges)

        doc._.context_graph = context_graph

        return doc
