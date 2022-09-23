from __future__ import annotations
import json
from typing import Optional, Dict, Union

from medspacy.section_detection.section_rule import SectionRule
import srsly


class Section(object):
    """
    Section is the object that stores the result of processing by the Sectionizer class. A Section contains information
    describing the section's category, title span, body span, parent, and the rule that created it.

    Section `category` is equivalent to `label_` in a basic spaCy entity. It is a normalized name for the section type
    determined on initialization, either created manually or through the Sectionizer pipeline component.

    Section title, defined with `title_start`, `title_end`, and `title_span` represents the section title or header
    matched with the rule. In the text "Past medical history: stroke and high blood pressure", "Past medical history:"
    would be the title.

    Section body is defined with `body_start`, `body_end`, and `body_span`. It represents the text between the end of
    the current section's title and the start of the title for the next Section or when scope is set in the rule or by
    the Sectionizer. In the text "Past medical history: stroke and high blood pressure", "stroke and high blood
    pressure" would be the body.

    Parent is a string that represents the conceptual "parent" section in a section->subsection->subsubsection
    hierarchy. Candidates are determined by category in the rule and matched at runtime.
    """

    def __init__(
        self,
        category: Union[str, None],
        title_start: int,
        title_end: int,
        body_start: int,
        body_end: int,
        parent: Optional[str] = None,
        rule: Optional[SectionRule] = None,
    ):
        """
        Create a new Section object.

        Args:
            category: A normalized name for the section. Equivalent to `label_` for basic spaCy entities.
            title_start: Index of the first token of the section title.
            title_end: Index of the last token of the section title.
            body_start: Index of the first token of the section body.
            body_end: Index of the last token of the section body.
            parent: The category of the parent section.
            rule: The SectionRule that generated the section.
        """
        self.category = category
        self.title_start = title_start
        self.title_end = title_end
        self.body_start = body_start
        self.body_end = body_end
        self.parent = parent
        self.rule = rule

    def __repr__(self):
        return (
            f"Section(category={self.category} at {self.title_start} : {self.title_end} in the doc with a body at "
            f"{self.body_start} : {self.body_end} based on the rule {self.rule}"
        )

    @property
    def title_span(self):
        """
        Gets the span of the section title.

        Returns:
            A tuple (int,int) containing the start and end indexes of the section title.
        """
        return self.title_start, self.title_end

    @property
    def body_span(self):
        """
        Gets the span of the section body.

        Returns:
            A tuple (int,int) containing the start and end indexes of the section body.
        """
        return self.body_start, self.body_end

    @property
    def section_span(self):
        """
        Gets the span of the entire section, from title start to body end.

        Returns:
            A tuple (int,int) containing the start index of the section title and the end index of the section body.
        """
        return self.title_start, self.body_end

    def serialized_representation(self):
        """
        Serialize the Section.

        Returns:
            A json-serialized representation of the section.
        """
        rule = self.rule

        return {
            "category": self.category,
            "title_start": self.title_start,
            "title_end": self.title_end,
            "body_start": self.body_start,
            "body_end": self.body_end,
            "parent": self.parent,
            "rule": rule.to_dict() if rule is not None else None,
        }

    @classmethod
    def from_serialized_representation(cls, serialized_representation: Dict[str, str]):
        """
        Load the section from a json-serialized form.

        Args:
            serialized_representation: The dictionary form of the section object to load.

        Returns:
            A Section object containing the data from the dictionary provided.
        """
        rule = SectionRule.from_dict(serialized_representation["rule"])
        section = Section(
            **{k: v for k, v in serialized_representation.items() if k not in ["rule"]}
        )
        section.rule = rule

        return section


@srsly.msgpack_encoders("section")
def serialize_section(obj, chain=None):
    if isinstance(obj, Section):
        return {"section": obj.serialized_representation()}
    return obj if chain is None else chain(obj)


@srsly.msgpack_decoders("section")
def deserialize_section(obj, chain=None):
    if "section" in obj:
        return Section.from_serialized_representation(obj["section"])
    return obj if chain is None else chain(obj)
