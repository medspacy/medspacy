from typing import Union, Iterable, Optional, Dict, Any, Tuple, List, Literal, Set

from spacy.tokens import Span, Doc
from spacy.language import Language

# Filepath to default rules which are included in package
from os import path
from pathlib import Path
import re
import warnings

from . import util
from .section_rule import SectionRule
from .section import Section
from ..common.medspacy_matcher import MedspacyMatcher

DEFAULT_RULES_FILEPATH = path.join(
    Path(__file__).resolve().parents[2],
    "resources",
    "section_patterns.json",
)

DEFAULT_ATTRS = {
    "past_medical_history": {"is_historical": True},
    "sexual_and_social_history": {"is_historical": True},
    "family_history": {"is_family": True},
    "patient_instructions": {"is_hypothetical": True},
    "education": {"is_hypothetical": True},
    "allergy": {"is_hypothetical": True},
}


@Language.factory("medspacy_sectionizer")
class Sectionizer:
    """
    The Sectionizer will search for spans in the text which match section header rules, such as 'Past Medical History:'.
    Sections will be represented in custom attributes as:
        category: A normalized title of the section. Example: 'past_medical_history'
        section_title: The Span of the doc which was matched as a section header.
            Example: 'Past Medical History:'
        section_span: The entire section of the note, starting with section_header and up until the end
            of the section, which will be either the start of the next section header of some pre-specified
            scope. Example: 'Past Medical History: Type II DM'

    Section attributes will be registered for each Doc, Span, and Token in the following attributes:
        Doc._.sections: A list of namedtuples of type Section with 4 elements:
            - section_title
            - section_header
            - section_parent
            - section_span.
        A Doc will also have attributes corresponding to lists of each
            (ie., Doc._.section_titles, Doc._.section_headers, Doc._.section_parents, Doc._.section_list)
        (Span|Token)._.section_title
        (Span|Token)._.section_header
        (Span|Token)._.section_parent
        (Span|Token)._.section_span
    """

    def __init__(
        self,
        nlp: Language,
        name: str = "medspacy_sectionizer",
        rules: Union[Iterable[SectionRule], Literal["default"], None] = "default",
        max_section_length: Optional[int] = None,
        phrase_matcher_attr: str = "LOWER",
        require_start_line: bool = False,
        require_end_line: bool = False,
        newline_pattern: str = r"[\n\r]+[\s]*$",
        input_span_type: Union[Literal["ents", "group"], None] = "ents",
        span_group_name: str = "medspacy_spans",
        span_attrs: Union[
            Literal["default"], Dict[str, Dict[str, Any]], None
        ] = "default",
    ):
        """
        Create a new Sectionizer component.

        Args:
            nlp: A SpaCy Language object.
            name: The name of the component.
            rules: The rules to load. Default is "default", loads rules packaged with medspaCy that are derived from
                SecTag, MIMIC-III, and practical refinement at the US Department of Veterans Affairs. If None, no rules
                are loaded. Otherwise, must be a list of SectionRule objects.
            max_section_length: Optional argument specifying the maximum number of tokens following a section header
                which can be included in a section body. This can be useful if you think your section rules are
                incomplete and want to prevent sections from running too long in the note. Default is None, meaning that
                the scope of a section will be until either the next section header or the end of the document.
            phrase_matcher_attr: The token attribute to use for PhraseMatcher for rules where `pattern` is None. Default
                is 'LOWER'.
            require_start_line: Optionally require a section header to start on a new line. Default False.
            require_end_line: Optionally require a section header to end with a new line. Default False.
            newline_pattern: Regular expression to match the new line either preceding or following a header
                if either require_start_line or require_end_line are True. Default is r"[\n\r]+[\s]*$"
            span_attrs: The optional span attributes to modify. Default option "default" uses attributes in
                `DEFAULT_ATTRIBUTES`. If a dictionary of custom attributes, format is a dictionary mapping section
                categories to a dictionary containing the attribute name and the value to set the attribute to when a
                span is contained in a section of that category. Custom attributes must be assigned with
                `Span.set_extension` before creating the Sectionizer. If None, sectionizer will not modify span
                attributes.
            input_span_type: "ents" or "group". Where to look for spans when modifying attributes of spans
                contained in a section if `span_attrs` is not None. "ents" will modify attributes of spans in doc.ents.
                "group" will modify attributes of spans in the span group specified by `span_group_name`.
            span_group_name: The name of the span group used when `input_span_type` is "group". Default is
                "medspacy_spans".
        """
        self.nlp = nlp
        self.name = name
        self.max_section_length = max_section_length
        self.require_start_line = require_start_line
        self.require_end_line = require_end_line
        self.newline_pattern = re.compile(newline_pattern)
        self.assertion_attributes_mapping = None
        self._parent_sections = {}
        self._parent_required = {}
        self.input_span_type = input_span_type
        self.span_group_name = span_group_name

        self.__matcher = MedspacyMatcher(nlp, phrase_matcher_attr=phrase_matcher_attr)

        if rules and rules == "default":
            self.add(SectionRule.from_json(DEFAULT_RULES_FILEPATH))
        elif rules:
            self.add(rules)

        if span_attrs == "default":
            self.assertion_attributes_mapping = DEFAULT_ATTRS
            self.register_default_attributes()
        elif span_attrs:
            for _, attr_dict in span_attrs.items():
                for attr_name in attr_dict.keys():
                    if not Span.has_extension(attr_name):
                        raise ValueError(
                            f"Custom extension {attr_name} has not been set. Please ensure Span.set_extension is "
                            f"called for your pipeline's custom extensions."
                        )
            self.assertion_attributes_mapping = span_attrs

    @property
    def rules(self) -> List[SectionRule]:
        """
        Gets list of rules associated with the Sectionizer.

        Returns:
            The list of SectionRules associated with the Sectionizer.
        """
        return self.__matcher.rules

    @property
    def section_categories(self) -> Set[str]:
        """
        Gets a list of categories used in the Sectionizer.

        Returns:
                The list of all section categories available to the Sectionizer.
        """
        return self.__matcher.labels

    @classmethod
    def register_default_attributes(cls):
        """
        Register the default values for the Span attributes defined in `DEFAULT_ATTRIBUTES`.
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

    def add(self, rules):
        """
        Adds SectionRules to the Sectionizer.

        Args:
            rules: A single SectionRule or a collection of SectionRules to add to the Sectionizer.
        """
        if isinstance(rules, SectionRule):
            rules = [rules]

        for rule in rules:
            if not isinstance(rule, SectionRule):
                raise TypeError("Rules must be SectionRule, not", type(rule))

        self.__matcher.add(rules)

        for rule in rules:
            name = rule.category
            parents = rule.parents
            parent_required = rule.parent_required
            if parents:
                if name in self._parent_sections.keys():
                    warnings.warn(
                        f"Duplicate section title {name}. Merging parents. "
                        f"If this is not intended, please specify distinct titles.",
                        RuntimeWarning,
                    )
                    self._parent_sections[name].update(parents)
                else:
                    self._parent_sections[name] = set(parents)

            if (
                name in self._parent_required.keys()
                and self._parent_required[name] != parent_required
            ):
                warnings.warn(
                    f"Duplicate section title {name} has different parent_required option. "
                    f"Setting parent_required to False.",
                    RuntimeWarning,
                )
                self._parent_required[name] = False
            else:
                self._parent_required[name] = parent_required

    def set_parent_sections(
        self, sections: List[Tuple[int, int, int]]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Determine the legal parent-child section relationships from the list
        of in-order sections of a document and the possible parents of each
        section as specified during direction creation.

        Args:
            sections: a list of spacy match tuples found in the doc

        Returns:
            A list of tuples (match_id, start, end, parent_idx) where the first three indices are the same as the input
            and the added parent_idx represents the index in the list that corresponds to the parent section. Might be a
            smaller list than the input due to pruning with `parent_required`.
        """
        sections_final = []
        removed_sections = 0
        for i, (match_id, start, end) in enumerate(sections):
            name = self.__matcher.rule_map[self.nlp.vocab.strings[match_id]].category
            required = self._parent_required[name]
            i_a = i - removed_sections  # adjusted index for removed values
            if required and i_a == 0:
                removed_sections += 1
                continue
            elif i_a == 0 or name not in self._parent_sections.keys():
                sections_final.append((match_id, start, end, None))
            else:
                parents = self._parent_sections[name]
                identified_parent = None
                for parent in parents:
                    # go backwards through the section "tree" until you hit a root or the start of the list
                    candidate = self.__matcher.rule_map[
                        self.nlp.vocab.strings[sections_final[i_a - 1][0]]
                    ].category
                    candidates_parent_idx = sections_final[i_a - 1][3]
                    if candidates_parent_idx is not None:
                        candidates_parent = self.__matcher.rule_map[
                            self.nlp.vocab.strings[
                                sections_final[candidates_parent_idx][0]
                            ]
                        ].category
                    else:
                        candidates_parent = None
                    candidate_i = i_a - 1
                    while candidate:
                        if candidate == parent:
                            identified_parent = candidate_i
                            candidate = None
                        else:
                            # if you are at the end of the list... no parent
                            if candidate_i < 1:
                                candidate = None
                                continue
                            # if the current candidate has no parent... no parent exists
                            if not candidates_parent:
                                candidate = None
                                continue
                            # otherwise get the previous item in the list
                            temp = self.__matcher.rule_map[
                                self.nlp.vocab.strings[
                                    sections_final[candidate_i - 1][0]
                                ]
                            ].category
                            temp_parent_idx = sections_final[candidate_i - 1][3]
                            if temp_parent_idx is not None:
                                temp_parent = self.__matcher.rule_map[
                                    self.nlp.vocab.strings[
                                        sections_final[temp_parent_idx][0]
                                    ]
                                ].category
                            else:
                                temp_parent = None
                            # if the previous item is the parent of the current item
                            # OR if the previous item is a sibling of the current item
                            # continue to search
                            if (
                                temp == candidates_parent
                                or temp_parent == candidates_parent
                            ):
                                candidate = temp
                                candidates_parent = temp_parent
                                candidate_i -= 1
                            # otherwise, there is no further tree traversal
                            else:
                                candidate = None

                # if a parent is required, then add
                if identified_parent is not None or not required:
                    # if the parent is identified, add section
                    # if the parent is not required, add section
                    # if parent is not identified and required, do not add the section
                    sections_final.append((match_id, start, end, identified_parent))
                else:
                    removed_sections += 1
        return sections_final

    def set_assertion_attributes(self, spans: Iterable[Span]):
        """
        Add Span-level attributes to entities based on which section they occur in.

        Args:
            spans: the spans to modify.
        """
        for span in spans:
            if (
                span._.section
                and span._.section.category in self.assertion_attributes_mapping
            ):
                attr_dict = self.assertion_attributes_mapping[span._.section.category]
                for (attr_name, attr_value) in attr_dict.items():
                    setattr(span._, attr_name, attr_value)

    def __call__(self, doc: Doc) -> Doc:
        """
        Call the Sectionizer on a spaCy doc. Sectionizer will identify sections using provided rules, then evaluate any
        section hierarchy as needed, create section spans, and modify attributes on existing spans based on the sections
        the entities spans in.

        Args:
            doc: The Doc to process.

        Returns:
            The processed spaCy Doc.
        """
        matches = self.__matcher(doc)
        if self.require_start_line:
            matches = self.filter_start_lines(doc, matches)
        if self.require_end_line:
            matches = self.filter_end_lines(doc, matches)
        if self._parent_sections:
            matches = self.set_parent_sections(matches)

        # If this has already been processed by the sectionizer, reset the sections
        doc._.sections = []
        # if there were no matches, return the doc as one section
        if len(matches) == 0:
            doc._.sections.append(Section(None, 0, 0, 0, len(doc)))
            return doc

        section_list = []
        # if the first match does not begin at token 0, handle the first section
        first_match = matches[0]
        if first_match[1] != 0:
            section_list.append(Section(None, 0, 0, 0, first_match[1]))

        # handle section spans
        for i, match in enumerate(matches):
            parent = None
            if len(match) == 4:
                (match_id, start, end, parent_idx) = match
                if parent_idx is not None:
                    parent = section_list[parent_idx]
            else:
                # IDEs will warn here about match shape disagreeing w/ type hinting, but this if is only used if
                # parent sections were never set, so parent_idx does not exist
                (match_id, start, end) = match
            rule = self.__matcher.rule_map[self.nlp.vocab.strings[match_id]]
            category = rule.category
            # If this is the last match, it should include the rest of the doc
            if i == len(matches) - 1:
                # If there is no scope limitation, go until the end of the doc
                if self.max_section_length is None and rule.max_scope is None:
                    section_list.append(
                        Section(category, start, end, end, len(doc), parent, rule)
                    )
                else:
                    # If the rule has a max_scope, use that as a precedence
                    if rule.max_scope is not None:
                        scope_end = min(end + rule.max_scope, doc[-1].i + 1)
                    else:
                        scope_end = min(end + self.max_section_length, doc[-1].i + 1)

                    section_list.append(
                        Section(category, start, end, end, scope_end, parent, rule)
                    )
            # Otherwise, go until the next section header
            else:
                next_match = matches[i + 1]
                _, next_start, _, _ = next_match
                if self.max_section_length is None and rule.max_scope is None:
                    section_list.append(
                        Section(category, start, end, end, next_start, parent, rule)
                    )
                else:
                    if rule.max_scope is not None:
                        scope_end = min(end + rule.max_scope, next_start)
                    else:
                        scope_end = min(end + self.max_section_length, next_start)
                    section_list.append(
                        Section(category, start, end, end, scope_end, parent, rule)
                    )

        for section in section_list:
            doc._.sections.append(section)
            start, end = section.section_span
            for token in doc[start:end]:
                token._.section = section

        # If it is specified to add assertion attributes,
        # iterate through the entities in doc and add them
        if self.assertion_attributes_mapping:
            if self.input_span_type.lower() == "ents":
                self.set_assertion_attributes(doc.ents)
            elif self.input_span_type.lower() == "group":
                self.set_assertion_attributes(doc.spans[self.span_group_name])

        return doc

    def filter_start_lines(
        self, doc: Doc, matches: List[Tuple[int, int, int]]
    ) -> List[Tuple[int, int, int]]:
        """
        Filter a list of matches to only contain spans where the start token is the beginning of a new line.

        Returns:
            A list of match tuples (match_id, start, end) that meet the filter criteria.
        """
        return [
            m for m in matches if util.is_start_line(m[1], doc, self.newline_pattern)
        ]

    def filter_end_lines(
        self, doc: Doc, matches: List[Tuple[int, int, int]]
    ) -> List[Tuple[int, int, int]]:
        """
        Filter a list of matches to only contain spans where the start token is followed by a new line.

        Returns:
            A list of match tuples (match_id, start, end) that meet the filter criteria.
        """
        return [
            m for m in matches if util.is_end_line(m[2] - 1, doc, self.newline_pattern)
        ]
