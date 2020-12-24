"""The ConTextComponent definiton."""
from os import path

# Filepath to default rules which are included in package
from pathlib import Path

from spacy.matcher import Matcher, PhraseMatcher
from spacy.tokens import Doc, Span

from .context_modifier import ConTextModifier
from .context_graph import ConTextGraph
from .context_rule import ConTextRule

from ..common.medspacy_matcher import MedspacyMatcher

#
DEFAULT_ATTRS = {
    "NEGATED_EXISTENCE": {"is_negated": True},
    "POSSIBLE_EXISTENCE": {"is_uncertain": True},
    "HISTORICAL": {"is_historical": True},
    "HYPOTHETICAL": {"is_hypothetical": True},
    "FAMILY": {"is_family": True},
}

DEFAULT_RULES_FILEPATH = path.join(Path(__file__).resolve().parents[2], "resources", "context_rules.json")


class ConTextComponent:
    """The ConTextComponent for spaCy processing."""

    name = "context"

    def __init__(
        self,
        nlp,
        targets="ents",
        add_attrs=True,
        phrase_matcher_attr="LOWER",
        rules="default",
        rule_list=None,
        allowed_types=None,
        excluded_types=None,
        use_context_window=False,
        max_scope=None,
        max_targets=None,
        terminations=None,
        prune=True,
        remove_overlapping_modifiers=False,
    ):

        """Create a new ConTextComponent algorithm.

        This component matches modifiers in a Doc,
        defines their scope, and identifies edges between targets and modifiers.
        Sets two spaCy extensions:
            - Span._.modifiers: a list of ConTextModifier objects which modify a target Span
            - Doc._.context_graph: a ConText graph object which contains the targets,
                modifiers, and edges between them.

        Args:
            nlp: a spaCy NLP model
            targets: the attribute of Doc which contains targets.
                Default is "ents", in which case it will use the standard Doc.ents attribute.
                Otherwise will look for a custom attribute in Doc._.{targets}
            add_attrs: Whether or not to add the additional spaCy Span attributes (ie., Span._.x)
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
            prune: Whether or not to prune modifiers which are substrings of another modifier.
                For example, if "no history of" and "history of" are both ConTextItems, both will match
                the text "no history of afib", but only "no history of" should modify afib.
                If True, will drop shorter substrings completely.
                Default True.
            remove_overlapping_modifiers: Whether or not to remove any matched modifiers which overlap
                with target entities. If False, any overlapping modifiers will not modify the overlapping
                entity but will still modify any other targets in its scope.
                Default False.
            rules: Which rules to load on initialization. Default is 'default'.
                - 'default': Load the default set of rules provided with cyConText
                - 'other': Load a custom set of rules, please also set rule_list with a file path or list.
                - None: Load no rules.
            rule_list: The location of rules in json format or a list of ContextItems. Default
                is None.
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
            terminations (dict or None): Optional mapping between different categories which will
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

        self.nlp = nlp
        if targets != "ents":
            raise NotImplementedError()
        self._target_attr = targets
        self.prune = prune
        self.remove_overlapping_modifiers = remove_overlapping_modifiers

        self._rules = []
        self._i = 0
        self._categories = set()

        self.matcher = MedspacyMatcher(nlp, phrase_matcher_attr=phrase_matcher_attr)
        # _modifier_rule_mapping: A mapping from spaCy Matcher match_ids to ConTextRule
        # This allows us to use spaCy Matchers while still linking back to the ConTextRule
        # To get the direction and category
        self._modifier_rule_mapping = self.matcher._rule_item_mapping
        # self.phrase_matcher = PhraseMatcher(
        #     nlp.vocab, attr=phrase_matcher_attr, validate=True
        # )  # TODO: match on custom attributes
        # self.matcher = Matcher(nlp.vocab, validate=True)
        # self.regex_matcher = RegexMatcher(nlp.vocab)

        self.register_graph_attributes()
        if add_attrs is False:
            self.add_attrs = False
        elif add_attrs is True:
            self.add_attrs = True
            self.context_attributes_mapping = DEFAULT_ATTRS
        elif isinstance(add_attrs, dict):
            # Check that each of the attributes being added has been set
            for modifier in add_attrs.keys():
                attr_dict = add_attrs[modifier]
                for attr_name, attr_value in attr_dict.items():
                    if not Span.has_extension(attr_name):
                        raise ValueError("Custom extension {0} has not been set. Call Span.set_extension.".format(attr_name))

            self.add_attrs = True
            self.context_attributes_mapping = add_attrs

        else:
            raise ValueError("add_attrs must be either True (default), False, or a dictionary, not {0}".format(add_attrs))
        if use_context_window is True:
            if not isinstance(max_scope, int) or max_scope < 1:
                raise ValueError(
                    "If 'use_context_window' is True, 'max_scope' must be an integer greater 1, " "not {0}".format(max_scope)
                )
        self.use_context_window = use_context_window
        if max_scope is not None and (not isinstance(max_scope, int) or max_scope < 1):
            raise ValueError("'max_scope' must be None or an integer greater 1, " "not {0}".format(max_scope))
        self.max_scope = max_scope

        self.allowed_types = allowed_types
        self.excluded_types = excluded_types
        self.max_targets = max_targets

        if terminations is None:
            terminations = dict()
        self.terminations = {k.upper(): v for (k, v) in terminations.items()}

        if rules == "default":

            rules = ConTextRule.from_json(DEFAULT_RULES_FILEPATH)
            self.add(rules)

        elif rules == "other":
            # use custom rules
            if isinstance(rule_list, str):
                # if rules_list is a string, then it must be a path to a json
                if "yaml" in rule_list or "yml" in rule_list:
                    try:
                        rule_list = ConTextRule.from_yaml(rule_list)
                    except:
                        raise ValueError("direction list {0} could not be read".format(rule_list))
                elif path.exists(rule_list):
                    rules = ConTextRule.from_json(rule_list)
                    self.add(rules)
                else:
                    raise ValueError("rule_list must be a valid path. Currently is: {0}".format(rule_list))

            elif isinstance(rule_list, list):
                # otherwise it is a list of contextrules
                if not rule_list:
                    raise ValueError("rule_list must not be empty.")
                for rule in rule_list:
                    # check that all rules are contextrules
                    if not isinstance(rule, ConTextRule):
                        raise ValueError(
                            "rule_list must contain only ContextItems. Currently contains: {0}".format(type(rule))
                        )
                self.add(rule_list)

            else:
                raise ValueError(
                    "rule_list must be a valid path or list of ContextItems. Currenty is: {0}".format(type(rule_list))
                )

        elif not rules:
            # otherwise leave the list empty.
            # do nothing
            self._rules = []

        else:
            # loading from json path or list is possible later
            raise ValueError("rules must either be 'default' (default), 'other' or None.")

    @property
    def rules(self):
        """Returns list of ConTextItems"""
        return self._rules

    @property
    def categories(self):
        """Returns list of categories from ConTextItems"""
        return self._categories

    def add(self, rules):
        """Add a list of ConTextRule rules to ConText.

        Args:
            rules: a list of ConTextItems to add.
        """
        try:
            self._rules += rules
        except TypeError:
            raise TypeError(
                "rules must be a list of ConText rules. If you're just passing in a single ConText Item, "
                "make sure to wrap the direction in a list: `context.add([direction])`"
            )
        self.matcher.add(rules)
        for rule in rules:
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
                if getattr(rule, attr) is None:  # If the direction itself has it defined, don't override
                    setattr(rule, attr, value)

            # Check custom termination points
            if rule.category.upper() in self.terminations:
                for other_modifier in self.terminations[rule.category.upper()]:
                    rule.terminated_by.add(other_modifier.upper())

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

    def __call__(self, doc):
        """Applies the ConText algorithm to a Doc.

        Args:
            doc: a spaCy Doc

        Returns:
            doc: a spaCy Doc
        """
        if self._target_attr == "ents":
            targets = doc.ents
        else:
            targets = getattr(doc._, self._target_attr)

        # Store data in ConTextGraph object
        # TODO: move some of this over to ConTextGraph
        context_graph = ConTextGraph(remove_overlapping_modifiers=self.remove_overlapping_modifiers)

        context_graph.targets = targets

        context_graph.modifiers = []
        matches = self.matcher(doc)

        for (match_id, start, end) in matches:
            # Get the ConTextRule object defining this modifier
            rules = self._modifier_rule_mapping[self.nlp.vocab[match_id].text]
            modifier = ConTextModifier(rules, start, end, doc, self.use_context_window)
            context_graph.modifiers.append(modifier)

        if self.prune:
            context_graph.prune_modifiers()
        context_graph.update_scopes()
        context_graph.apply_modifiers()

        # Link targets to their modifiers
        for target, modifier in context_graph.edges:
            target._.modifiers += (modifier,)

        # If add_attrs is True, add is_negated, is_current, is_asserted to targets
        if self.add_attrs:
            self.set_context_attributes(context_graph.edges)

        doc._.context_graph = context_graph

        return doc
