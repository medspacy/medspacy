class Section(object):
    def __init__(self, doc, category, title_start, title_end, body_start, body_end, parent=None, rule=None):
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
