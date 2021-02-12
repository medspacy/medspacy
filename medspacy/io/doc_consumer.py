from collections import OrderedDict

ALLOWED_DATA_TYPES = ("ent", "section", "doc")

ALLOWED_SECTION_ATTRS = {
            "section_category",
            "section_title_text",
            "section_title_start_char",
            "section_title_end_char",
            "section_title_text",
            "section_title_start_char",
            "section_title_end_char",
            "section_text",
            "section_text_start_char",
            "section_text_end_char",
            "section_parent",


        }


class DocConsumer:
    """A DocConsumer object will consume a spacy doc and output rows based on a configuration provided by the user."""
    
    name = "doc_consumer"

    def __init__(self, nlp, data_types=("ent",), attrs=None, sectionizer=False, context=False):
        self.nlp = nlp
        for dtype in data_types:
            if dtype not in ALLOWED_DATA_TYPES:
                raise ValueError("Invalid data_types. Supported data_types are {0}, not {1}".format(ALLOWED_DATA_TYPES, dtype))
            if dtype == "section":
                self.validate_section_attrs(attrs)
        self.data_types = data_types
        self.attrs = attrs
        # self.section_attrs = []
        self.sectionizer = sectionizer
        self.context = context

        if self.attrs is None:
            # basic ent attrs
            self.attrs = {dtype: list() for dtype in data_types}
            if "ent" in self.attrs:
                self.attrs["ent"] = ["text", "start_char", "end_char", "label_"]

                if self.context:
                    self.attrs["ent"] += ["is_negated", "is_uncertain", "is_historical", "is_hypothetical", "is_family"]

                if self.sectionizer:
                    self.attrs["ent"] += ["section_category", "section_parent"]
            if "section" in self.attrs:
                self.attrs["section"] += [
                    "section_category",
                    "section_title_text",
                    "section_title_start_char",
                    "section_title_end_char",
                    "section_text",
                    "section_text_start_char",
                    "section_text_end_char",
                    "section_parent",
                ]
            if "doc" in self.attrs:
                self.attrs["doc"] += ["text"]

    def validate_section_attrs(self, attrs):
        """Validate that section attributes are either not specified or are valid attribute names."""
        if attrs is None:
            return True
        if "section" not in attrs:
            return True
        diff = set(attrs["section"]).difference(ALLOWED_SECTION_ATTRS)
        if diff:
            raise ValueError("Invalid section attrs specified: {0}".format(diff))
        return True

    def __call__(self, doc):
        data = dict()
        for dtype, attrs in self.attrs.items():
            data.setdefault(dtype, OrderedDict())
            for attr in attrs:
                data[dtype][attr] = list()
        if "ent" in self.data_types:
            for ent in doc.ents:
                for attr in self.attrs["ent"]:
                    try:
                        val = getattr(ent, attr)
                    except AttributeError:
                        val = getattr(ent._, attr)
                    data["ent"][attr].append(val)

        if "section" in self.data_types:
            for section in doc._.sections:
                self.add_section_attributes(section, data["section"])
        if "doc" in self.data_types:
            for attr in self.attrs["doc"]:
                try:
                    val = getattr(doc, attr)
                except AttributeError:
                    val = getattr(doc._, attr)
                data["doc"][attr].append(val)

        doc._.data = data
        return doc

    def add_section_attributes(self, section, section_data):
        # Allow for null sections
        section_data["section_category"].append(section.category)
        if section.category is not None:
            section_data["section_title_text"].append(section.title_span.text)
            section_data["section_title_start_char"].append(section.title_span.start_char)
            section_data["section_title_end_char"].append(section.title_span.end_char)
        else:
            section_data["section_title_text"].append(None)
            section_data["section_title_start_char"].append(0)
            section_data["section_title_end_char"].append(0)
        section_data["section_text"].append(section.section_span.text)
        section_data["section_text_start_char"].append(section.section_span.start_char)
        section_data["section_text_end_char"].append(section.section_span.end_char)
        section_data["section_parent"].append(section.parent)






        # for attr in self.section_attrs:
        #     section_data[attr] = []
        # ent_data = {}
        # for attr in self.attrs:
        #     ent_data[attr] = []
        # for ent in doc.ents:
        #     for attr in self.attrs:
        #         try:
        #             val = getattr(ent, attr)
        #         except AttributeError:
        #             val = getattr(ent._, attr)
        #         ent_data[attr].append(val)
        # doc._.ent_data = ent_data
        # if self.sectionizer:
        #
        #     for section in doc._.sections:
        #         section_data["section_category"].append(section.category)
        #         if section.category is not None:
        #             section_data["section_title_text"].append(section.title_span.text)
        #             section_data["section_title_start_char"].append(section.title_span.start_char)
        #             section_data["section_title_end_char"].append(section.title_span.end_char)
        #         else:
        #             section_data["section_title_text"].append(None)
        #             section_data["section_title_start_char"].append(0)
        #             section_data["section_title_end_char"].append(0)
        #         section_data["section_text"].append(section.section_span.text)
        #         section_data["section_text_start_char"].append(section.section_span.start_char)
        #         section_data["section_text_end_char"].append(section.section_span.end_char)
        #         section_data["section_parent"].append(section.parent)
        #     doc._.section_data = section_data
        # return doc
