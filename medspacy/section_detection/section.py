import json


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
        return f"""Section(category={self.category}, title={self.title_span}, body={self.body_span}, parent={self.parent}, rule={self.rule})"""

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
