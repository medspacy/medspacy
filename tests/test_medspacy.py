import pytest

import medspacy
import spacy


class TestMedSpaCy:
    def test_default_build_pipe_names(self):
        model, enable, disable = medspacy.util._build_pipe_names("default", enable=None, disable=None)
        assert model == "en_core_web_sm"
        assert enable == {"tokenizer", "sentencizer", "target_matcher", "context"}
        assert disable == {"parser", "tagger", "ner"}

    def test_default_load(self):
        nlp = medspacy.load()
        expected_pipe_names = {
            "sentencizer",
            "context",
            "target_matcher",
        }
        assert set(nlp.pipe_names) == expected_pipe_names

    def test_load_enable(self):
        nlp = medspacy.load(enable={"target_matcher", "sectionizer"})
        assert len(nlp.pipeline) == 2
        assert set(nlp.pipe_names) == {"target_matcher", "sectionizer"}

    def test_nlp(self):
        nlp = medspacy.load()
        assert nlp("This is a sentence. So is this.")

    def test_load_disable(self):
        nlp = medspacy.load(disable=["context"])
        expected_pipe_names = {
            "sentencizer",
            "target_matcher",
        }
        assert set(nlp.pipe_names) == expected_pipe_names

    def test_load_all_components(self):
        full_pipe_names = [
            "sentencizer",
            "target_matcher",
            "context",
            "sectionizer",
            "postprocessor"
        ]

        nlp = medspacy.load(enable="all")
        assert nlp.pipe_names == full_pipe_names
        assert isinstance(nlp.tokenizer, medspacy.preprocess.Preprocessor)

    # def test_load_sci(self):
    #     # pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.3.0/en_core_sci_sm-0.3.0.tar.gz
    #     assert medspacy.load("en_core_sci_sm")

    def test_load_rules(self):
        nlp = medspacy.load(load_rules=True)
        context = nlp.get_pipe("context")
        assert context.item_data

    def test_not_load_rules(self):
        nlp = medspacy.load(load_rules=False)
        context = nlp.get_pipe("context")
        assert not context.item_data

    def test_medspacy_tokenizer(self):
        default_tokenizer = spacy.blank("en").tokenizer
        custom_tokenizer = medspacy.load(enable=['tokenizer']).tokenizer

        text = r'Pt c\o n;v;d h\o chf+cp n/v/d'

        default_doc = default_tokenizer(text)
        medspacy_doc = custom_tokenizer(text)

        assert [token.text for token in default_doc] != [token.text for token in medspacy_doc]

        # Check that some expected token boundries are generated
        joined_tokens = " ".join([token.text for token in medspacy_doc])
        assert "c \\ o" in joined_tokens
        assert "n / v / d" in joined_tokens
        assert "chf + cp" in joined_tokens

    def test_disable_medspacy_tokenizer(self):
        default_tokenizer = spacy.blank("en").tokenizer
        custom_tokenizer = medspacy.load(disable=['tokenizer']).tokenizer

        text = r'Pt c\o n;v;d h\o chf+cp n/v/d'

        default_doc = default_tokenizer(text)
        medspacy_doc = custom_tokenizer(text)

        assert [token.text for token in default_doc] == [token.text for token in medspacy_doc]

    def test_medspacy_tokenizer_uppercase(self):
        custom_tokenizer = medspacy.load(enable=['tokenizer']).tokenizer

        # Issue 13: Ensure that uppercase tokens are not tokenized as each character
        # https://github.com/medspacy/medspacy/issues/13
        text = r'DO NOT BREAK ME UP'

        medspacy_doc = custom_tokenizer(text)

        tokens = [token.text for token in medspacy_doc]

        assert len(tokens) == 5

        # Check that some expected token boundries are generated
        joined_tokens = " ".join(tokens)
        assert "DO NOT BREAK ME UP" in joined_tokens
        assert "B R E A K" not in joined_tokens

    def test_medspacy_tokenizer_numerics(self):
        custom_tokenizer = medspacy.load(enable=['tokenizer']).tokenizer

        text = r'1.5 mg'

        medspacy_doc = custom_tokenizer(text)

        tokens = [token.text for token in medspacy_doc]

        assert len(tokens) == 2

        # Check that some expected token boundries are generated
        joined_tokens = " ".join(tokens)
        assert "1.5" in joined_tokens
        assert "1 . 5" not in joined_tokens

