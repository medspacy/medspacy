import spacy
from spacy.tokens import Doc, Span, Token

from . import util


Doc.set_extension("ent_data", default=dict(), force=True)
Doc.set_extension("section_data", default=dict(), force=True)

Doc.set_extension("get_data", method=util.get_data, force=True)


class DocConsumer(object):
    """A DocConsumer object will consume a spacy doc and output rows based on a configuration provided by the user."""

    def __init__(self, nlp, attrs=None, sectionizer=False, context=False):
        super(DocConsumer, self).__init__()
        self.nlp = nlp
        self.attrs = attrs
        self.section_attrs = []
        self.sectionizer = sectionizer
        self.context = context

        if self.attrs is None:
            # basic ent attrs
            self.attrs = ["text", "start_char", "end_char", "label_"]

            if self.context:
                self.attrs += ["is_negated", "is_uncertain", "is_historical", "is_hypothetical", "is_family"]

            if self.sectionizer:
                self.attrs += ["section_title", "section_parent"]
                self.section_attrs += [
                    "section_title",
                    "section_title_text",
                    "section_title_start_char",
                    "section_title_end_char",
                    "section_text",
                    "section_text_start_char",
                    "section_text_end_char",
                    "section_parent",
                ]

    def __call__(self, doc):
        section_data = {}
        for attr in self.section_attrs:
            section_data[attr] = []
        ent_data = {}
        for attr in self.attrs:
            ent_data[attr] = []
        for ent in doc.ents:
            for attr in self.attrs:
                try:
                    val = getattr(ent, attr)
                except AttributeError:
                    val = getattr(ent._, attr)
                ent_data[attr].append(val)
        doc._.ent_data = ent_data
        if self.sectionizer:
            for (title, title_text, parent, section) in doc._.sections:
                section_data["section_title"].append(title)
                if title is not None:
                    section_data["section_title_text"].append(title_text.text)
                    section_data["section_title_start_char"].append(title_text.start_char)
                    section_data["section_title_end_char"].append(title_text.end_char)
                else:
                    section_data["section_title_text"].append(None)
                    section_data["section_title_start_char"].append(0)
                    section_data["section_title_end_char"].append(0)
                section_data["section_text"].append(section.text)
                section_data["section_text_start_char"].append(section.start_char)
                section_data["section_text_end_char"].append(section.end_char)
                section_data["section_parent"].append(parent)
            doc._.section_data = section_data
        return doc
