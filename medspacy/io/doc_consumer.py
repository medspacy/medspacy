from collections import OrderedDict
from typing import Tuple, Dict, Optional

from spacy.language import Language
from spacy.tokens import Span

from medspacy.context import ConTextModifier

ALLOWED_DATA_TYPES = ("ents", "group", "section", "context", "doc")

DEFAULT_ENT_ATTRS = (
    "text",
    "start_char",
    "end_char",
    "label_",
    "is_negated",
    "is_uncertain",
    "is_historical",
    "is_hypothetical",
    "is_family",
    "section_category",
    "section_parent",
)

DEFAULT_DOC_ATTRS = ("text",)

ALLOWED_SECTION_ATTRS = (
    "section_category",
    "section_title_text",
    "section_title_start_char",
    "section_title_end_char",
    "section_body",
    "section_body_start_char",
    "section_body_end_char",
    "section_parent",
)

ALLOWED_CONTEXT_ATTRS = (
    "ent_text",
    "ent_label_",
    "ent_start_char",
    "ent_end_char",
    "modifier_text",
    "modifier_category",
    "modifier_direction",
    "modifier_start_char",
    "modifier_end_char",
    "modifier_scope_start_char",
    "modifier_scope_end_char",
)

DEFAULT_ATTRS = {
    "ents": DEFAULT_ENT_ATTRS,
    "group": DEFAULT_ENT_ATTRS,
    "section": ALLOWED_SECTION_ATTRS,
    "context": ALLOWED_CONTEXT_ATTRS,
    "doc": DEFAULT_DOC_ATTRS,
}


@Language.factory("medspacy_doc_consumer")
class DocConsumer:
    """
    A DocConsumer object will consume a spacy doc and output rows based on a configuration provided by the user.

    This component extracts structured information from a Doc. Information is stored in doc._.data, which is a
        nested dictionary. The outer keys represent the data type of can one or more of:
            - "ents": data about the spans in doc.ents such as the text, label,
                context attributes, section information, or custom attributes
            - "group": data about spans in a span group with the name `span_group_attrs` section text and category
            - "context": data about entity-modifier pairs extracted by ConText
            - "doc": a single doc-level representation. By default only doc.text is extracted, but other attributes may
                be specified

        Once processed, a doc's data can be accessed either by:
            - doc._.data
            - doc._.get_data(dtype=...)
            - doc._.ent_data
            - doc._.to_dataframe(dtype=...)
    """

    def __init__(
        self,
        nlp,
        name: str = "medspacy_doc_consumer",
        dtypes: Tuple = ("ents",),
        dtype_attrs: Dict = None,
        span_group_name: str = "medspacy_spans",
    ):
        """
        Creates a new DocConsumer.

        Args:
            nlp: A spaCy model
            dtypes: Either a tuple of data types to collect or the string "all". Default ("ents",). Valid  options are:
                "ents", "group", "section", "context", "doc".
            dtype_attrs: An optional dictionary mapping the data types in dtypes to a list of attributes. If None, will
                set defaults for each dtype. Attributes for "ents", "group", and "doc" may be customized be adding either
                native or custom attributes (i.e., ent._....) "context" and "section" are not customizable at this time.
                Default values for each dtype can be retrieved by the class method `DocConsumer.get_default_attrs()
            span_group_name: the name of the span group used when dtypes contains "group". At this time, only one span
                group is supported.
        """
        self.nlp = nlp
        self.name = name
        self._span_group_name = span_group_name
        if not isinstance(dtypes, tuple):
            if dtypes == "all":
                dtypes = tuple(ALLOWED_DATA_TYPES)
            else:
                raise ValueError(
                    "dtypes must be either 'all' or a tuple, not {0}".format(dtypes)
                )
        for dtype in dtypes:
            if dtype not in ALLOWED_DATA_TYPES:
                raise ValueError(
                    "Invalid dtypes. Supported dtypes are {0}, not {1}".format(
                        ALLOWED_DATA_TYPES, dtype
                    )
                )
            if dtype == "section":
                self.validate_section_attrs(dtype_attrs)
        self.dtypes = dtypes
        self.dtype_attrs = dtype_attrs

        if self.dtype_attrs is None:
            self._set_default_attrs()

    @classmethod
    def get_default_attrs(cls, dtypes: Optional[Tuple] = None):
        """
        Gets the default attributes available to each type specified.

        Args:
            dtypes: Optional tuple containing "ents", "group", "context", "section", or "doc". If None, all will be
                returned.

        Returns:
            The attributes the doc consumer will output for each of the specified types in `dtypes`.
        """
        if dtypes is None:
            dtypes = ALLOWED_DATA_TYPES
        else:
            if isinstance(dtypes, str):
                dtypes = (dtypes,)
            for dtype in dtypes:
                if dtype not in ALLOWED_DATA_TYPES:
                    raise ValueError("Invalid dtype,", dtype)
        dtype_attrs = {
            dtype: list(attrs)
            for (dtype, attrs) in DEFAULT_ATTRS.items()
            if dtype in dtypes
        }
        return dtype_attrs

    def _set_default_attrs(self):
        """
        Gets the default attributes.
        """
        self.dtype_attrs = self.get_default_attrs(self.dtypes)

    def validate_section_attrs(self, attrs):
        """
        Validate that section attributes are either not specified or are valid attribute names.
        """
        if attrs is None:
            return True
        if "section" not in attrs:
            return True
        diff = set(attrs["section"]).difference(ALLOWED_SECTION_ATTRS)
        if diff:
            raise ValueError("Invalid section dtype_attrs specified: {0}".format(diff))
        return True

    def __call__(self, doc):
        """
        Call the doc consumer on a doc and assign the data.

        Args:
            doc: The Doc to process.

        Returns:
            The processed Doc.
        """
        data = dict()
        for dtype, attrs in self.dtype_attrs.items():
            data.setdefault(dtype, OrderedDict())
            for attr in attrs:
                data[dtype][attr] = list()
        if "ents" in self.dtypes:
            for ent in doc.ents:
                for attr in self.dtype_attrs["ents"]:
                    try:
                        val = getattr(ent, attr)
                    except AttributeError:
                        val = getattr(ent._, attr)
                    data["ents"][attr].append(val)
        if "group" in self.dtypes:
            for span in doc.spans[self._span_group_name]:
                for attr in self.dtype_attrs["ents"]:
                    try:
                        val = getattr(span, attr)
                    except AttributeError:
                        val = getattr(span._, attr)
                    data["group"][attr].append(val)
        if "context" in self.dtypes:
            for (ent, modifier) in doc._.context_graph.edges:
                self.add_context_edge_attributes(ent, modifier, data["context"], doc)
        if "section" in self.dtypes:
            for section in doc._.sections:
                self.add_section_attributes(section, data["section"], doc)
        if "doc" in self.dtypes:
            for attr in self.dtype_attrs["doc"]:
                try:
                    val = getattr(doc, attr)
                except AttributeError:
                    val = getattr(doc._, attr)
                data["doc"][attr].append(val)

        doc._.data = data
        return doc

    def add_context_edge_attributes(
        self, ent: Span, modifier: ConTextModifier, context_data, doc
    ):
        span_tup = modifier.modifier_span
        span = doc[span_tup[0] : span_tup[1]]
        scope_tup = modifier.scope_span
        scope = doc[scope_tup[0] : scope_tup[1]]
        for attr in self.dtype_attrs["context"]:
            if attr == "ent_text":
                context_data["ent_text"].append(ent.text)
            elif attr == "ent_label_":
                context_data["ent_label_"].append(ent.label_)
            elif attr == "ent_start_char":
                context_data["ent_start_char"].append(ent.start_char)
            elif attr == "ent_end_char":
                context_data["ent_end_char"].append(ent.end_char)
            elif attr == "modifier_text":
                context_data["modifier_text"].append(span.text)
            elif attr == "modifier_category":
                context_data["modifier_category"].append(modifier.category)
            elif attr == "modifier_direction":
               context_data["modifier_direction"].append(modifier.direction)
            elif attr == "modifier_start_char":
                context_data["modifier_start_char"].append(span.start_char)
            elif attr == "modifier_end_char":
                context_data["modifier_end_char"].append(span.end_char)
            elif attr == "modifier_scope_start_char":
                context_data["modifier_scope_start_char"].append(scope.start_char)
            elif attr == "modifier_scope_end_char":
                context_data["modifier_scope_end_char"].append(scope.end_char)
            else:
            # if specified attribute is not one of these standard values, check the entity to see if it's an entity value
                try:
                    val = getattr(ent, attr)
                except AttributeError:
                    try:
                        val = getattr(ent._, attr)
                    except AttributeError:
                        raise ValueError(f"Attributes for dtype 'context' must be either "
                                         f"a registered custom Span attribute (i.e., Span._.attr) or one of these pre-defined values: "
                                          f"{ALLOWED_CONTEXT_ATTRS}. \nYou passed in '{attr}'")
                context_data[f"ent_{attr}"] = val

    def add_section_attributes(self, section, section_data, doc):
        # Allow for null sections
        section_title_tup = section.title_span
        section_body_tup = section.body_span
        section_title = doc[section_title_tup[0] : section_title_tup[1]]
        section_body = doc[section_body_tup[0] : section_body_tup[1]]
        if "section_category" in self.dtype_attrs["section"]:
            section_data["section_category"].append(section.category)
        if section.category is not None:
            if "section_title_text" in self.dtype_attrs["section"]:
                section_data["section_title_text"].append(section_title.text)
            if "section_title_start_char" in self.dtype_attrs["section"]:
                section_data["section_title_start_char"].append(
                    section_title.start_char
                )
            if "section_title_end_char" in self.dtype_attrs["section"]:
                section_data["section_title_end_char"].append(section_title.end_char)
        else:
            if "section_title_text" in self.dtype_attrs["section"]:
                section_data["section_title_text"].append(None)
            if "section_title_start_char" in self.dtype_attrs["section"]:
                section_data["section_title_start_char"].append(0)
            if "section_title_end_char" in self.dtype_attrs["section"]:
                section_data["section_title_end_char"].append(0)
        if "section_body" in self.dtype_attrs["section"]:
            section_data["section_body"].append(section_body.text)
        if "section_body_start_char" in self.dtype_attrs["section"]:
            section_data["section_body_start_char"].append(section_body.start_char)
        if "section_body_end_char" in self.dtype_attrs["section"]:
            section_data["section_body_end_char"].append(section_body.end_char)
        if "section_parent" in self.dtype_attrs["section"]:
            section_data["section_parent"].append(section.parent)
