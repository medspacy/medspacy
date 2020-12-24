from spacy.tokens import Doc, Token, Span

# Filepath to default rules which are included in package
from os import path
from pathlib import Path
import re
import warnings

from . import util
from .section_rule import SectionRule
from .section import Section
from ..common.medspacy_matcher import MedspacyMatcher

Doc.set_extension("sections", default=list(), force=True)
Doc.set_extension("section_categories", getter=util.get_section_categories, force=True)
Doc.set_extension("section_titles", getter=util.get_section_title_spans, force=True)
Doc.set_extension("section_bodies", getter=util.get_section_body_spans, force=True)
Doc.set_extension("section_parents", getter=util.get_section_parents, force=True)

Token.set_extension("section", default=None, force=True)

# Set span attributes to the attribute of the first token
# in case there is some overlap between a span and a new section header
Span.set_extension("section", getter=lambda x: x[0]._.section_category, force=True)

DEFAULT_RULES_FILEPATH = path.join(Path(__file__).resolve().parents[2], "resources", "section_patterns.json",)

DEFAULT_ATTRS = {
    "past_medical_history": {"is_historical": True},
    "sexual_and_social_history": {"is_historical": True},
    "family_history": {"is_family": True},
    "patient_instructions": {"is_hypothetical": True},
    "education": {"is_hypothetical": True},
    "allergy": {"is_hypothetical": True},
}


class Sectionizer:
    name = "sectionizer"

    def __init__(
        self,
        nlp,
        patterns="default",
        add_attrs=False,
        max_scope=None,
        include_header=False,
        phrase_matcher_attr="LOWER",
        require_start_line=False,
        require_end_line=False,
        newline_pattern=r"[\n\r]+[\s]*$",
    ):
        """Create a new Sectionizer component. The sectionizer will search for spans in the text which
        match section header patterns, such as 'Past Medical History:'. Sections will be represented
        in custom attributes as:
            section_title (str): A normalized title of the section. Example: 'past_medical_history'
            section_header (Span): The Span of the doc which was matched as a section header.
                Example: 'Past Medical History:'
            section (Span): The entire section of the note, starting with section_header and up until the end
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

        Args:
            nlp: A SpaCy language model object
            patterns (str, list, or None): Where to read patterns from. Default is "default", which will
                load the default patterns provided by medSpaCy, which are derived from MIMIC-II.
                If a list, should be a list of pattern dicts following these conventional spaCy formats:
                    [
                        {"section_title": "past_medical_history", "pattern": "Past Medical History:"},
                        {"section_title": "problem_list", "pattern": [{"TEXT": "PROBLEM"}, {"TEXT": "LIST"}, {"TEXT": ":"}]}
                    ]
                If a string other than "default", should be a path to a jsonl file containing patterns.
            max_scope (None or int): Optional argument specifying the maximum number of tokens following a section header
                which can be included in a section. This can be useful if you think your section patterns are incomplete
                and want to prevent sections from running too long in the note. Default is None, meaning that the scope
                of a section will be until either the next section header or the end of the document.
            include_title (bool): whether the section title is included in the section text
            phrase_matcher_attr (str): The name of the token attribute which will be used by the PhraseMatcher
                for any patterns with a "pattern" value of a string.
            require_start_line (bool): Optionally require a section header to start on a new line. Default False.
            require_end_line (bool): Optionally require a section header to end with a new line. Default False.
            newline_pattern (str): Regular expression to match the new line either preceding or following a header
                if either require_start_line or require_end_line are True.
        """
        self.nlp = nlp
        self.add_attrs = add_attrs
        self.matcher = MedspacyMatcher(nlp, phrase_matcher_attr=phrase_matcher_attr)
        self.max_scope = max_scope
        self.require_start_line = require_start_line
        self.require_end_line = require_end_line
        self.newline_pattern = re.compile(newline_pattern)
        self.assertion_attributes_mapping = None
        self._parent_sections = {}
        self._parent_required = {}
        self._rule_item_mapping = self.matcher._rule_item_mapping
        self.include_header = include_header

        if patterns is not None:
            if patterns == "default":
                import os

                if not os.path.exists(DEFAULT_RULES_FILEPATH):
                    raise FileNotFoundError(
                        "The expected location of the default patterns file cannot be found. Please either "
                        "add patterns manually or add a jsonl file to the following location: ",
                        DEFAULT_RULES_FILEPATH,
                    )
                self.add(SectionRule.from_json(DEFAULT_RULES_FILEPATH))
            # If a list, add each of the patterns in the list
            elif isinstance(patterns, list):
                self.add(patterns)
            elif isinstance(patterns, str):
                path.exists(patterns)
                self.add(SectionRule.from_json(patterns))

        if add_attrs is False:
            self.add_attrs = False
        elif add_attrs is True:
            self.assertion_attributes_mapping = DEFAULT_ATTRS
            self.register_default_attributes()
        elif isinstance(add_attrs, dict):
            # Check that each of the attributes being added has been set
            for modifier in add_attrs.keys():
                attr_dict = add_attrs[modifier]
                for attr_name, attr_value in attr_dict.items():
                    if not Span.has_extension(attr_name):
                        raise ValueError("Custom extension {0} has not been set. Call Span.set_extension.")

            self.add_attrs = True
            self.assertion_attributes_mapping = add_attrs

        else:
            raise ValueError("add_attrs must be either True (default), False, or a dictionary, not {0}".format(add_attrs))

    def register_default_attributes(self):
        """Register the default values for the Span attributes defined in DEFAULT_ATTRS."""
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

    def add(self, patterns):
        """Add a list of patterns to the clinical_sectionizer. Each pattern should be a dictionary with
       two keys:
           'section': The normalized section name of the section, such as 'pmh'.
           'pattern': The spaCy pattern matching a span of text.
               Either a string for exact matching (case insensitive)
               or a list of dicts.

       Example:
       >>> patterns = [ \
           {"section_title": "past_medical_history", "pattern": "pmh"}\
           {"section_title": "past_medical_history", "pattern": [{"LOWER": "past", "OP": "?"}, \
               {"LOWER": "medical"}, \
               {"LOWER": "history"}]\
               },\
           {"section_title": "assessment_and_plan", "pattern": "a/p:"}\
           ]
       >>> clinical_sectionizer.add(patterns)
       """
        if not isinstance(patterns, list):
            patterns = [patterns]

        self.matcher.add(patterns)

        for pattern in patterns:
            name = pattern.category
            parents = pattern.parents
            parent_required = pattern.parent_required

            if name in self._parent_sections.keys() and parents != []:
                warnings.warn(
                    "Duplicate section title {0}. Merging parents. If this is not indended, please specify distinc titles.".format(
                        name
                    ),
                    RuntimeWarning,
                )
                self._parent_sections[name].update(parents)
            else:
                self._parent_sections[name] = set(parents)

            if name in self._parent_required.keys() and self._parent_required[name] != parent_required:
                warnings.warn(
                    "Duplicate section title {0} has different parent_required option. Setting parent_required to False.".format(
                        name
                    ),
                    RuntimeWarning,
                )
                self._parent_required[name] = False
            else:
                self._parent_required[name] = parent_required

    def set_parent_sections(self, sections):
        """Determine the legal parent-child section relationships from the list
        of in-order sections of a document and the possible parents of each
        section as specified during direction creation.

        Args:
            sections: a list of spacy match tuples found in the doc
        """
        sections_final = []
        removed_sections = 0
        for i, (match_id, start, end) in enumerate(sections):
            name = self._rule_item_mapping[self.nlp.vocab.strings[match_id]].category
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
                    candidate = self._rule_item_mapping[self.nlp.vocab.strings[sections_final[i_a - 1][0]]].category
                    candidates_parent = sections_final[i_a - 1][3]
                    candidate_i = i_a - 1
                    while candidate:
                        if candidate == parent:
                            # identified_parent = parent
                            identified_parent = i_a - 1
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
                            temp = self.nlp.vocab.strings[sections_final[candidate_i - 1][0]]
                            temp_parent = sections_final[candidate_i - 1][3]
                            # if the previous item is the parent of the current item
                            # OR if the previous item is a sibling of the current item
                            # continue to search
                            if temp == candidates_parent or temp_parent == candidates_parent:
                                candidate = temp
                                candidates_parent = temp_parent
                                candidate_i -= 1
                            # otherwise, there is no further tree traversal
                            else:
                                candidate = None

                # if a parent is required, then add
                if identified_parent or not required:
                    # if the parent is identified, add section
                    # if the parent is not required, add section
                    # if parent is not identified and required, do not add the section
                    sections_final.append((match_id, start, end, identified_parent))
                else:
                    removed_sections += 1
        return sections_final

    def set_assertion_attributes(self, ents):
        """Add Span-level attributes to entities based on which section they occur in.

        Args:
            edges: the edges to modify

        """
        for ent in ents:
            if ent._.section_title in self.assertion_attributes_mapping:
                attr_dict = self.assertion_attributes_mapping[ent._.section_title]
                for (attr_name, attr_value) in attr_dict.items():
                    setattr(ent._, attr_name, attr_value)

    def __call__(self, doc):
        matches = self.matcher(doc)
        if self.require_start_line:
            matches = self.filter_start_lines(doc, matches)
        if self.require_end_line:
            matches = self.filter_end_lines(doc, matches)
        matches = self.set_parent_sections(matches)

        # If this has already been processed by the sectionizer, reset the sections
        doc._.sections = []
        # if there were no matches, return the doc as one section
        if len(matches) == 0:
            doc._.sections.append(Section(doc, None, 0, 0, 0, len(doc)))
            return doc

        section_list = []
        # if the firt match does not begin at token 0, handle the first section
        first_match = matches[0]
        if first_match[1] != 0:
            section_list.append(Section(doc, None, 0, 0, 0, first_match[1]))

        # handle section spans
        for i, match in enumerate(matches):
            (match_id, start, end, parent_idx) = match
            if parent_idx is not None:
                parent = section_list[parent_idx]
            else:
                parent = None
            rule = self._rule_item_mapping[self.nlp.vocab.strings[match_id]]
            category = self._rule_item_mapping[self.nlp.vocab.strings[match_id]].category
            # If this is the last match, it should include the rest of the doc
            if i == len(matches) - 1:
                if self.max_scope is None:
                    section_list.append(Section(doc, category, start, end, end, len(doc), parent, rule))
                else:
                    scope_end = min(end + self.max_scope, doc[-1].i)
                    section_list.append(Section(doc, category, start, end, end, scope_end, parent, rule))
            # Otherwise, go until the next section header
            else:
                next_match = matches[i + 1]
                _, next_start, _, _ = next_match
                if self.max_scope is None:
                    section_list.append(Section(doc, category, start, end, end, next_start, parent, rule))
                else:
                    scope_end = min(end + self.max_scope, next_start)
                    section_list.append(Section(doc, category, start, end, end, scope_end, parent, rule))

        for section in section_list:
            doc._.sections.append(section)
            for token in section.section_span:
                token._.section = section

        # If it is specified to add assertion attributes,
        # iterate through the entities in doc and add them
        if self.add_attrs is True:
            self.set_assertion_attributes(doc.ents)
        return doc

    def filter_start_lines(self, doc, matches):
        "Filter a list of matches to only contain spans where the start token is the beginning of a new line."
        return [m for m in matches if util.is_start_line(m[1], doc, self.newline_pattern)]

    def filter_end_lines(self, doc, matches):
        "Filter a list of matches to only contain spans where the start token is followed by a new line."
        return [m for m in matches if util.is_end_line(m[2] - 1, doc, self.newline_pattern)]
