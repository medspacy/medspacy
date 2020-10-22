class Preprocessor:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.rules = []

    def add(self, rules):
        self.rules += rules

    def __call__(self, text):
        for rule in self.rules:
            text = rule(text)

        return self.tokenizer(text)





