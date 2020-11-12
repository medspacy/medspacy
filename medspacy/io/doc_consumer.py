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
        self._ent_data = {}
        self._section_data = {}

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
                for attr in self.section_attrs:
                    self._section_data[attr] = []

        for attr in self.attrs:
            self._ent_data[attr] = []

    def __call__(self, doc):
        for ent in doc.ents:
            for attr in self.attrs:
                try:
                    val = getattr(ent, attr)
                except AttributeError:
                    try:
                        val = getattr(ent._, attr)
                    except AttributeError:
                        print("failed to get {0}".format(attr))
                        val = None
                self._ent_data[attr].append(val)
        doc._.ent_data = self._ent_data
        if self.sectionizer:
            for (title, title_text, parent, section) in doc._.sections:
                self._section_data["section_title"].append(title)
                if title is not None:
                    self._section_data["section_title_text"].append(title_text.text)
                    self._section_data["section_title_start_char"].append(title_text.start_char)
                    self._section_data["section_title_end_char"].append(title_text.end_char)
                else:
                    self._section_data["section_title_text"].append(None)
                    self._section_data["section_title_start_char"].append(0)
                    self._section_data["section_title_end_char"].append(0)
                self._section_data["section_text"].append(section.text)
                self._section_data["section_text_start_char"].append(section.start_char)
                self._section_data["section_text_start_char"].append(section.end_char)
                self._section_data["section_parent"].append(parent)
            doc._.section_data = self._section_data
        return doc
