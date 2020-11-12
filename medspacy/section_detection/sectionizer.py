from spacy.tokens import Doc, Token, Span
from spacy.matcher import Matcher, PhraseMatcher

# Filepath to default rules which are included in package
from os import path
from pathlib import Path
import re
import warnings

from . import util

Doc.set_extension("sections", default=list(), force=True)
Doc.set_extension("section_titles", getter=util.get_section_titles, force=True)
Doc.set_extension("section_headers", getter=util.get_section_headers, force=True)
Doc.set_extension("section_spans", getter=util.get_section_spans, force=True)
Doc.set_extension("section_parents", getter=util.get_section_parents, force=True)

Token.set_extension("section_span", default=None, force=True)
Token.set_extension("section_title", default=None, force=True)
Token.set_extension("section_header", default=None, force=True)
Token.set_extension("section_parent", default=None, force=True)

# Set span attributes to the attribute of the first token
# in case there is some overlap between a span and a new section header
Span.set_extension("section_span", getter=lambda x: x[0]._.section_span, force=True)
Span.set_extension("section_title", getter=lambda x: x[0]._.section_title, force=True)
Span.set_extension("section_header", getter=lambda x: x[0]._.section_header, force=True)
Span.set_extension("section_parent", getter=lambda x: x[0]._.section_parent, force=True)

DEFAULT_RULES_FILEPATH = path.join(Path(__file__).resolve().parents[2], "resources", "section_patterns.jsonl",)

DEFAULT_ATTRS = {
    "past_medical_history": {"is_historical": True},
    "sexual_and_social_history": {"is_historical": True},
    "family_history": {"is_family": True},
    "patient_instructions": {"is_hypothetical": True},
    "education": {"is_hypothetical": True},
    "allergy": {"is_hypothetical": True},
}
from collections import namedtuple

Section = namedtuple("Section", field_names=["section_title", "section_header", "section_parent", "section_span"])


class Sectionizer:
    name = "sectionizer"

    def __init__(
        self,
        nlp,
        patterns="default",
        add_attrs=False,
        max_scope=None,
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
                (ie., Doc._.section_titles, Doc._.section_headers, Doc._.section_parents, Doc._.section_spans)
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
            phrase_matcher_attr (str): The name of the token attribute which will be used by the PhraseMatcher
                for any patterns with a "pattern" value of a string.
            require_start_line (bool): Optionally require a section header to start on a new line. Default False.
            require_end_line (bool): Optionally require a section header to end with a new line. Default False.
            newline_pattern (str): Regular expression to match the new line either preceding or following a header
                if either require_start_line or require_end_line are True.
        """
        self.nlp = nlp
        self.add_attrs = add_attrs
        self.matcher = Matcher(nlp.vocab)
        self.max_scope = max_scope
        self.phrase_matcher = PhraseMatcher(nlp.vocab, attr=phrase_matcher_attr)
        self.require_start_line = require_start_line
        self.require_end_line = require_end_line
        self.newline_pattern = re.compile(newline_pattern)
        self.assertion_attributes_mapping = None
        self._patterns = []
        self._section_titles = set()
        self._parent_sections = {}
        self._parent_required = {}

        if patterns is not None:
            if patterns == "default":
                import os

                if not os.path.exists(DEFAULT_RULES_FILEPATH):
                    raise FileNotFoundError(
                        "The expected location of the default patterns file cannot be found. Please either "
                        "add patterns manually or add a jsonl file to the following location: ",
                        DEFAULT_RULES_FILEPATH,
                    )
                self.add(self.load_patterns_from_jsonl(DEFAULT_RULES_FILEPATH))
            # If a list, add each of the patterns in the list
            elif isinstance(patterns, list):
                self.add(patterns)
            elif isinstance(patterns, str):
                import os

                assert os.path.exists(patterns)
                self.add(self.load_patterns_from_jsonl(patterns))

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

    @property
    def patterns(self):
        return self._patterns

    @property
    def section_titles(self):
        return self._section_titles

    @classmethod
    def load_patterns_from_jsonl(self, filepath):

        import json

        patterns = []
        with open(filepath) as f:
            for line in f:
                if line.startswith("//"):
                    continue
                patterns.append(json.loads(line))

        return patterns

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
        for pattern_dict in patterns:
            name = pattern_dict["section_title"]
            pattern = pattern_dict["pattern"]
            parents = []
            parent_required = False
            if "parents" in pattern_dict.keys():
                parents = pattern_dict["parents"]

            if "parent_required" in pattern_dict.keys():
                if not parents:
                    raise ValueError(
                        "Jsonl file incorrectly formatted for pattern name {0}. If parents are required, then at least one parent must be specified.".format(
                            name
                        )
                    )
                parent_required = pattern_dict["parent_required"]

            if isinstance(pattern, str):
                self.phrase_matcher.add(name, None, self.nlp.make_doc(pattern))
            else:
                self.matcher.add(name, [pattern])
            self._patterns.append(pattern_dict)
            self._section_titles.add(name)

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
        section as specified during rule creation.

        Args:
            sections: a list of spacy match tuples found in the doc
        """
        sections_final = []
        removed_sections = 0
        for i, (match_id, start, end) in enumerate(sections):
            name = self.nlp.vocab.strings[match_id]
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
                    candidate = self.nlp.vocab.strings[sections_final[i_a - 1][0]]
                    candidates_parent = sections_final[i_a - 1][3]
                    candidate_i = i_a - 1
                    while candidate:
                        if candidate == parent:
                            identified_parent = parent
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
        matches += self.phrase_matcher(doc)
        if self.require_start_line:
            matches = self.filter_start_lines(doc, matches)
        if self.require_end_line:
            matches = self.filter_end_lines(doc, matches)
        matches = prune_overlapping_matches(matches)
        matches = self.set_parent_sections(matches)
        # If this has already been processed by the sectionizer, reset the sections
        doc._.sections = []
        if len(matches) == 0:
            doc._.sections.append((None, None, None, doc[0:]))
            return doc

        first_match = matches[0]
        section_spans = []
        if first_match[1] != 0:
            section_spans.append(Section(None, None, None, doc[0 : first_match[1]]))
        for i, match in enumerate(matches):
            (match_id, start, end, parent) = match
            section_header = doc[start:end]
            name = self.nlp.vocab.strings[match_id]
            # If this is the last match, it should include the rest of the doc
            if i == len(matches) - 1:
                if self.max_scope is None:
                    section_spans.append(Section(name, section_header, parent, doc[start:]))
                else:
                    scope_end = min(end + self.max_scope, doc[-1].i)
                    section_spans.append(Section(name, section_header, parent, doc[start:scope_end]))
            # Otherwise, go until the next section header
            else:
                next_match = matches[i + 1]
                _, next_start, _, _ = next_match
                if self.max_scope is None:
                    section_spans.append(Section(name, section_header, parent, doc[start:next_start]))
                else:
                    scope_end = min(end + self.max_scope, next_start)
                    section_spans.append(Section(name, section_header, parent, doc[start:scope_end]))

        # section_spans_with_parent = self.set_parent_sections(section_spans)

        # if there are no sections after required rules remove them, add one section over the entire document and exit
        # if len(section_spans_with_parent) == 0:
        #     doc._.sections.append((None, None, None, doc[0:]))
        #     return doc

        for section_tuple in section_spans:
            name, header, parent, section = section_tuple
            doc._.sections.append(section_tuple)
            for token in section:
                token._.section_span = section
                token._.section_title = name
                token._.section_header = header
                token._.section_parent = parent

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
    if _span_overlaps(a, b) or _span_overlaps(b, a):
        return True
    return False


def _span_overlaps(a, b):
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
