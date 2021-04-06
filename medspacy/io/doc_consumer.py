from collections import OrderedDict

ALLOWED_DATA_TYPES = ("ent", "section", "context", "doc")

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
    "section_text",
    "section_text_start_char",
    "section_text_end_char",
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
    "ent": DEFAULT_ENT_ATTRS,
    "section": ALLOWED_SECTION_ATTRS,
    "context": ALLOWED_CONTEXT_ATTRS,
    "doc": DEFAULT_DOC_ATTRS,
}


class DocConsumer:
    """A DocConsumer object will consume a spacy doc and output rows based on a configuration provided by the user."""

    name = "doc_consumer"

    def __init__(self, nlp, dtypes=("ent",), dtype_attrs=None):
        """Create a new DocConsumer.

        This component extracts structured information from a Doc. Information is stored in
        doc._.data, which is a nested dictionary. The outer keys represent the data type of
        can be either:
            - "ent": data about the spans in doc.ents such as the text, label,
                context attributes, section information, or custom attributes
            - "section": data about the sections within the notes, such as the
                section text and category
            - "context": data about entity-modifier pairs extracted by ConText
            - "doc": a single doc-level representation. By default only doc.text is extracted,
                but other attributes may be specified

        Once processed, a doc's data can be accessed either by:
            - doc._.data
            - doc._.get_data(dtype=...)
            - doc._.ent_data
            - doc._.to_dataframe(dtype=...)

        Args:
            nlp: A spaCy model
            dtypes (tuple or str): Either a tuple of data types to collect or the string "all".
                Default ("ent",)
                Valid options are ("ent", "section", "context", "doc")

            dtype_attrs(dict or None): An optional dictionary mapping the data types in dtypes to a list
                of attributes. If None, will set defaults for each dtype. Attributes for "ent" and "doc"
                may be customized be adding either native or custom attributes (ie., ent._....)
                "context" and "section" may only include the attributes contained in the default.
                Default values for each dtype can be retrieved by the class method DocConsumer.get_default_attrs()
        """
        self.nlp = nlp
        if not isinstance(dtypes, tuple):
            if dtypes == "all":
                dtypes = tuple(ALLOWED_DATA_TYPES)
            else:
                raise ValueError("dtypes must be either 'all' or a tuple, not {0}".format(dtypes))
        for dtype in dtypes:
            if dtype not in ALLOWED_DATA_TYPES:
                raise ValueError("Invalid dtypes. Supported dtypes are {0}, not {1}".format(ALLOWED_DATA_TYPES, dtype))
            if dtype == "section":
                self.validate_section_attrs(dtype_attrs)
        self.dtypes = dtypes
        self.dtype_attrs = dtype_attrs

        if self.dtype_attrs is None:
            self.set_default_attrs()

    @classmethod
    def get_default_attrs(cls, dtypes=None):
        if dtypes is None:
            dtypes = ALLOWED_DATA_TYPES
        else:
            if isinstance(dtypes, str):
                dtypes = (dtypes,)
            for dtype in dtypes:
                if dtype not in ALLOWED_DATA_TYPES:
                    raise ValueError("Invalid dtype,", dtype)
        dtype_attrs = {dtype: list(attrs) for (dtype, attrs) in DEFAULT_ATTRS.items() if dtype in dtypes}
        return dtype_attrs

    def set_default_attrs(self):
        self.dtype_attrs = self.get_default_attrs(self.dtypes)

    def validate_section_attrs(self, attrs):
        """Validate that section attributes are either not specified or are valid attribute names."""
        if attrs is None:
            return True
        if "section" not in attrs:
            return True
        diff = set(attrs["section"]).difference(ALLOWED_SECTION_ATTRS)
        if diff:
            raise ValueError("Invalid section dtype_attrs specified: {0}".format(diff))
        return True

    def __call__(self, doc):
        data = dict()
        for dtype, attrs in self.dtype_attrs.items():
            data.setdefault(dtype, OrderedDict())
            for attr in attrs:
                data[dtype][attr] = list()
        if "ent" in self.dtypes:
            for ent in doc.ents:
                for attr in self.dtype_attrs["ent"]:
                    try:
                        val = getattr(ent, attr)
                    except AttributeError:
                        val = getattr(ent._, attr)
                    data["ent"][attr].append(val)
        if "context" in self.dtypes:
            for (ent, modifier) in doc._.context_graph.edges:
                self.add_context_edge_attributes(ent, modifier, data["context"])
        if "section" in self.dtypes:
            for section in doc._.sections:
                self.add_section_attributes(section, data["section"])
        if "doc" in self.dtypes:
            for attr in self.dtype_attrs["doc"]:
                try:
                    val = getattr(doc, attr)
                except AttributeError:
                    val = getattr(doc._, attr)
                data["doc"][attr].append(val)

        doc._.data = data
        return doc

    def add_context_edge_attributes(self, ent, modifier, context_data):
        if "ent_text" in self.dtype_attrs["context"]:
            context_data["ent_text"].append(ent.text)
        if "ent_label_" in self.dtype_attrs["context"]:
            context_data["ent_label_"].append(ent.label_)
        if "ent_start_char" in self.dtype_attrs["context"]:
            context_data["ent_start_char"].append(ent.start_char)
        if "ent_end_char" in self.dtype_attrs["context"]:
            context_data["ent_end_char"].append(ent.end_char)
        if "modifier_text" in self.dtype_attrs["context"]:
            context_data["modifier_text"].append(modifier.span.text)
        if "modifier_category" in self.dtype_attrs["context"]:
            context_data["modifier_category"].append(modifier.category)
        if "modifier_direction" in self.dtype_attrs["context"]:
            context_data["modifier_direction"].append(modifier.direction)
        if "modifier_start_char" in self.dtype_attrs["context"]:
            context_data["modifier_start_char"].append(modifier.span.start_char)
        if "modifier_end_char" in self.dtype_attrs["context"]:
            context_data["modifier_end_char"].append(modifier.span.end_char)
        if "modifier_scope_start_char" in self.dtype_attrs["context"]:
            context_data["modifier_scope_start_char"].append(modifier.scope.start_char)
        if "modifier_scope_end_char" in self.dtype_attrs["context"]:
            context_data["modifier_scope_end_char"].append(modifier.span.end_char)

    def add_section_attributes(self, section, section_data):
        # Allow for null sections
        if "section_category" in self.dtype_attrs["section"]:
            section_data["section_category"].append(section.category)
        if section.category is not None:
            if "section_title_text" in self.dtype_attrs["section"]:
                section_data["section_title_text"].append(section.title_span.text)
            if "section_title_start_char" in self.dtype_attrs["section"]:
                section_data["section_title_start_char"].append(section.title_span.start_char)
            if "section_title_end_char" in self.dtype_attrs["section"]:
                section_data["section_title_end_char"].append(section.title_span.end_char)
        else:
            if "section_title_text" in self.dtype_attrs["section"]:
                section_data["section_title_text"].append(None)
            if "section_title_start_char" in self.dtype_attrs["section"]:
                section_data["section_title_start_char"].append(0)
            if "section_title_end_char" in self.dtype_attrs["section"]:
                section_data["section_title_end_char"].append(0)
        if "section_text" in self.dtype_attrs["section"]:
            section_data["section_text"].append(section.section_span.text)
        if "section_text_start_char" in self.dtype_attrs["section"]:
            section_data["section_text_start_char"].append(section.section_span.start_char)
        if "section_text_end_char" in self.dtype_attrs["section"]:
            section_data["section_text_end_char"].append(section.section_span.end_char)
        if "section_parent" in self.dtype_attrs["section"]:
            section_data["section_parent"].append(section.parent)
