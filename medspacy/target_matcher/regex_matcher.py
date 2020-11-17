import re

class RegexMatcher:

    def __init__(self, vocab, flags=re.IGNORECASE, resolve_start="left", resolve_right="right"):
        self.vocab = vocab
        self._patterns = {}
        self.labels = set()
        self._rules = list()
        self._rule_item_mapping = dict()

    def add(self, match_id, patterns, on_match=None):
        if on_match is not None:
            raise NotImplementedError()

        if match_id not in self.vocab:
            self.vocab.strings.add(match_id)
        self._patterns.setdefault(self.vocab.strings[match_id], [])
        for pattern in patterns:
            self._patterns[self.vocab.strings[match_id]].append(re.compile(pattern))

    def get(self, key):
        return self._patterns.get(self.vocab.strings[key], [])

    def __call__(self, doc):
        matches = []
        for (match_id, patterns) in self._patterns.items():
            for pattern in patterns:
                re_matches = pattern.finditer(doc.text_with_ws)
                for match in re_matches:
                    print(match)
                    span = doc.char_span(match.start(), match.end())
                    if span is None:
                        start = get_token_for_char(doc, match.start(), resolve="left")
                        end = get_token_for_char(doc, match.end(), resolve="right")
                        span = doc[start.i:end.i]
                    matches.append((match_id, span.start, span.end))
        return matches


def get_token_for_char(doc, char_idx, resolve="left"):
    for i, token in enumerate(doc):
        if char_idx > token.idx:
            continue
        if char_idx == token.idx:
            return token
        if char_idx < token.idx:
            if resolve == "left":
                return doc[i - 1]
            elif resolve == "right":
                return doc[i]
            else:
                raise ValueError()