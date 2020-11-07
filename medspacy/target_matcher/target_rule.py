class TargetRule:
    def __init__(self, literal, category, pattern=None, attributes=None, on_match=None):
        self.literal = literal
        self.category = category
        self.pattern = pattern
        self.attributes = attributes
        self.on_match = on_match
        self._rule_id = None
        
    def __repr__(self):
        return f"""TargetRule(literal="{self.literal}", category="{self.category}", pattern={self.pattern}, attributes={self.attributes}, on_match={self.on_match})"""
