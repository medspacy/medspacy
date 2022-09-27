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
        use_context_window: bool = False,
        max_scope: Optional[int] = None,
        max_targets: Optional[int] = None,
        terminations: Optional[Dict[str, Iterable[str]]] = None,
        prune: bool = True,
        remove_overlapping_modifiers: bool = False,
        input_span_type: Union[Literal["ents", "group"]] = "ents",
        span_group_name: str = "medspacy_spans",
        span_attrs: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """

            add_attrs: Whether to add the additional spaCy Span attributes (ie., Span._.x)
                defining assertion on the targets. By default, these are:
                - is_negated: True if a target is modified by 'NEGATED_EXISTENCE', default False
                - is_uncertain: True if a target is modified by 'POSSIBLE_EXISTENCE', default False
                - is_historical: True if a target is modified by 'HISTORICAL', default False
                - is_hypothetical: True if a target is modified by 'HYPOTHETICAL', default False
                - is_family: True if a target is modified by 'FAMILY', default False
                In the future, these should be made customizable.
            phrase_matcher_attr: The token attribute to be used by the underlying PhraseMatcher.
                If "LOWER", then the matching of modifiers with a "literal" string will be
                case-insensitive. If "TEXT" or "ORTH", it will be case-sensitive.
                Default "LOWER'.
            prune: Whether to prune modifiers which are substrings of another modifier.
                For example, if "no history of" and "history of" are both ConTextItems, both will match
                the text "no history of afib", but only "no history of" should modify afib.
                If True, will drop shorter substrings completely.
                Default True.
            remove_overlapping_modifiers: Whether to remove any matched modifiers which overlap
                with target entities. If False, any overlapping modifiers will not modify the overlapping
                entity but will still modify any other targets in its scope.
                Default False.
            rules: Which rules to load on initialization. Default is 'default'.
                - 'default': Load the default set of rules provided with cyConText
                - 'other': Load a custom set of rules, please also set rule_list with a file path or list.
                - None: Load no rules.
            allowed_types (set or None): A set of target labels to allow a ConTextRule to modify.
                If None, will apply to any type not specifically excluded in excluded_types.
                Only one of allowed_types and excluded_types can be used. An error will be thrown
                if both or not None.
                If this attribute is also defined in the ConTextRule, it will keep that value.
                Otherwise it will inherit this value.
            excluded_types (set or None): A set of target labels which this modifier cannot modify.
                If None, will apply to all target types unless allowed_types is not None.
                If this attribute is also defined in the ConTextRule, it will keep that value.
                Otherwise it will inherit this value.
            max_targets (int or None): The maximum number of targets which a modifier can modify.
                If None, will modify all targets in its scope.
                If this attribute is also defined in the ConTextRule, it will keep that value.
                Otherwise it will inherit this value.
            use_context_window (bool): Whether to use a specified range around a target to check
                for modifiers rather than split sentence boundaries. This can be useful
                for quicker processing by skipping sentence splitting or errors caused by poorly
                defined sentence boundaries. If True, max_scope must be an integer greater than 0.
            max_scope (int or None): A number to explicitly limit the size of the modifier's scope
                If this attribute is also defined in the ConTextRule, it will keep that value.
                Otherwise it will inherit this value.
            terminations: Optional mapping between different categories which will
                cause one modifier type to be 'terminated' by another type. For example, if given
                a mapping:
                    {"POSITIVE_EXISTENCE": {"NEGATED_EXISTENCE", "UNCERTAIN"},
                    "NEGATED_EXISTENCE": {"FUTURE"},
                    }
                all modifiers of type "POSITIVE_EXISTENCE" will be terminated by "NEGATED_EXISTENCE" or "UNCERTAIN"
                modifiers, and all "NEGATED_EXISTENCE" modifiers will be terminated by "FUTURE".
                This can also be defined for specific ConTextItems in the `terminated_by` attribute.


        Returns:
            context: a ConTextComponent

        Raises:
            ValueError: if one of the parameters is incorrectly formatted.
        """
        """
        Create a new ConTextComponent.

        Args:
            nlp: A SpaCy Language object.
            name: The name of the component.
            rules: The rules to load. Default is "default", loads rules packaged with medspaCy that are derived from 
                original ConText rules and years of practical applications at the US Department of Veterans Affairs.  If 
                None, no rules are loaded. Otherwise, must be a list of ConTextRule objects.
            phrase_matcher_attr: The token attribute to use for PhraseMatcher for rules where `pattern` is None. Default
                is 'LOWER'.
            allowed_types: 
            excluded_types: 
            use_context_window: 
            max_scope: 
            max_targets: 
            terminations: 
            prune: 
            remove_overlapping_modifiers: 
            input_span_type: "ents" or "group". Where to look for targets. "ents" will modify attributes of spans 
                in doc.ents. "group" will modify attributes of spans in the span group specified by `span_group_name`.
            span_group_name: The name of the span group used when `input_span_type` is "group". Default is
                "medspacy_spans".
            span_attrs: The optional span attributes to modify. Format is a dictionary mapping context modifier 
                categories to a dictionary containing the attribute name and the value to set the attribute to when a 
                span is modified by a modifier of that category. Default behavior is to use attributes in 
                `DEFAULT_ATTRIBUTES`.
        """
        self.nlp = nlp
        self.name = name
        self.prune = prune
        self.remove_overlapping_modifiers = remove_overlapping_modifiers
        self.input_span_type = input_span_type
        self.span_group_name = span_group_name

        self._i = 0
        self._categories = set()

        self.__matcher = MedspacyMatcher(
            nlp, phrase_matcher_attr=phrase_matcher_attr, prune=prune
        )

        if span_attrs:
            for _, attr_dict in span_attrs.items():
                for attr_name in attr_dict.keys():
                    if not Span.has_extension(attr_name):
                        raise ValueError(
                            f"Custom extension {attr_name} has not been set. Please ensure Span.set_extension is "
                            f"called for your pipeline's custom extensions."
                        )
            self.assertion_attributes_mapping = span_attrs
        else:
            self.context_attributes_mapping = DEFAULT_ATTRIBUTES
            self.register_graph_attributes()

        if use_context_window is True:
            if not isinstance(max_scope, int) or max_scope < 1:
                raise ValueError(
                    f"If 'use_context_window' is True, 'max_scope' must be an integer greater than 0, not {max_scope}"
                )
        self.use_context_window = use_context_window

        if max_scope is not None and (not isinstance(max_scope, int) or max_scope < 1):
            raise ValueError(
                f"'max_scope' must be None or an integer greater than 0, not {max_scope}"
            )
        self.max_scope = max_scope

        self.allowed_types = allowed_types
        self.excluded_types = excluded_types
        self.max_targets = max_targets

        if terminations is None:
            terminations = dict()
        self.terminations = {k.upper(): v for (k, v) in terminations.items()}

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
        """Add a list of ConTextRule rules to ConText.

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
            if rule.category.upper() in self.terminations:
                for other_modifier in self.terminations[rule.category.upper()]:
                    rule.terminated_by.add(other_modifier.upper())

            self.__matcher.add(rules)

    def register_graph_attributes(self):
        """Register spaCy container custom attribute extensions.

        By default will register Span._.modifiers and Doc._.context_graph.

        If self.add_attrs is True, will add additional attributes to span
            as defined in DEFAULT_ATTRS:
            - is_negated
            - is_historical
            - is_experiencer
        """
        Span.set_extension("modifiers", default=(), force=True)
        Doc.set_extension("context_graph", default=None, force=True)

    def set_context_attributes(self, edges):
        """Add Span-level attributes to targets with modifiers.

        Args:
            edges: the edges to modify

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
        if self.input_span_type == "ents":
            targets = doc.ents
        elif self.input_span_type == "group":
            targets = doc.spans[self.span_group_name]
        else:
            targets = getattr(doc._, targets)
        # Store data in ConTextGraph object
        # TODO: move some of this over to ConTextGraph
        context_graph = ConTextGraph(
            remove_overlapping_modifiers=self.remove_overlapping_modifiers
        )

        context_graph.targets = targets

        context_graph.modifiers = []
        matches = self.__matcher(doc)

        for (match_id, start, end) in matches:
            # Get the ConTextRule object defining this modifier
            rules = self.__matcher.rule_map[self.nlp.vocab[match_id].text]
            modifier = ConTextModifier(rules, start, end, doc, self.use_context_window)
            context_graph.modifiers.append(modifier)

        context_graph.update_scopes()
        context_graph.apply_modifiers()

        # Link targets to their modifiers
        for target, modifier in context_graph.edges:
            target._.modifiers += (modifier,)

        # If add_attrs is True, add is_negated, is_current, is_asserted to targets
        if self.input_span_type:
            self.set_context_attributes(context_graph.edges)

        doc._.context_graph = context_graph

        return doc
