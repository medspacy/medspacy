import json
import pdb
import srsly
from medspacy.section_detection.section_rule import SectionRule

class Section(object):
    def __init__(
        self, doc, category, title_start, title_end, body_start, body_end, parent=None, rule=None
    ):
        self.doc = doc
        self.category = category
        self.title_start = title_start
        self.title_end = title_end
        self.body_start = body_start
        self.body_end = body_end
        self.parent = parent
        self.rule = rule

    def __repr__(self):
        if self.doc is not None:
            return f"""Section(category={self.category}, title={self.title_span}, body={self.body_span}, parent={self.parent}, rule={self.rule})"""
        else:
            return f"""Section(category={self.category} at {self.title_start} : {self.title_end} in the doc with a body at {self.body_start} : {self.body_end} based on the rule {self.rule}"""

    @property
    def title_span(self):
        return self.doc[self.title_start : self.title_end]

    @property
    def body_span(self):
        return self.doc[self.body_start : self.body_end]

    @property
    def section_span(self):
        return self.doc[self.title_start : self.body_end]

    def save(self, *args, **kwargs):
        raise ValueError

    def to_disk(self, path, **kwargs):
        # This will receive the directory path + /my_component
        data_path = path / "section.json"
        with data_path.open("w", encoding="utf8") as f:
            f.write(json.dumps(self.data))

    def from_disk(self, path, **cfg):
        # This will receive the directory path + /my_component
        data_path = path / "section.json"
        with data_path.open("r", encoding="utf8") as f:
            self.data = json.loads(f)
        return self


    def serialized_representation(self):

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
    def from_serialized_representation(cls, serialized_representation):
        rule = SectionRule.from_dict(serialized_representation["rule"])
        serialized_representation["doc"] = None #TODO: Unhack this

        section = Section(**{k:v for k,v in serialized_representation.items() if k not in ["rule"]})
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
