import pytest

import sys
import medspacy
import spacy

from medspacy.target_matcher import TargetRule


class TestMedSpaCy:
    def test_default_build_pipe_names(self):
        enable, disable = medspacy.util._build_pipe_names(
            enable="default", disable=None
        )
        assert enable == {
            "medspacy_tokenizer",
            "medspacy_pyrush",
            "medspacy_target_matcher",
            "medspacy_context",
        }
        assert disable == set()

    def test_default_load(self):
        nlp = medspacy.load()
        expected_pipe_names = {
            "medspacy_pyrush",
            "medspacy_context",
            "medspacy_target_matcher",
        }
        assert set(nlp.pipe_names) == expected_pipe_names

    def test_load_enable(self):
        nlp = medspacy.load(
            medspacy_enable={"medspacy_target_matcher", "medspacy_sectionizer"}
        )
        assert len(nlp.pipeline) == 2
        assert set(nlp.pipe_names) == {
            "medspacy_target_matcher",
            "medspacy_sectionizer",
        }

    def test_nlp(self):
        nlp = medspacy.load()
        assert nlp("This is a sentence. So is this.")

    def test_load_disable(self):
        nlp = medspacy.load(medspacy_disable=["medspacy_context"])
        expected_pipe_names = {
            "medspacy_pyrush",
            "medspacy_target_matcher",
        }
        assert set(nlp.pipe_names) == expected_pipe_names

    def test_load_all_component_names(self):
        expected_pipe_names = {
            "medspacy_tokenizer",
            "medspacy_preprocessor",
            "medspacy_pyrush",
            "medspacy_target_matcher",
            "medspacy_quickumls",
            "medspacy_context",
            "medspacy_sectionizer",
            "medspacy_postprocessor",
            "medspacy_doc_consumer",
        }
        actual_pipe_names, _ = medspacy.util._build_pipe_names("all")
        assert expected_pipe_names == actual_pipe_names

    def test_load_all_components(self):
        full_pipe_names = [
            "medspacy_pyrush",
            "medspacy_target_matcher",
            "medspacy_quickumls",
            "medspacy_context",
            "medspacy_sectionizer",
            "medspacy_postprocessor",
            "medspacy_doc_consumer",
        ]

        nlp = medspacy.load(medspacy_enable="all")
        assert nlp.pipe_names == full_pipe_names
        assert isinstance(nlp.tokenizer, medspacy.preprocess.Preprocessor)

    # def test_load_sci(self):
    #     # pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.3.0/en_core_sci_sm-0.3.0.tar.gz
    #     assert medspacy.load("en_core_sci_sm")

    def test_load_rules(self):
        nlp = medspacy.load(load_rules=True)
        context = nlp.get_pipe("medspacy_context")
        assert context.rules

    def test_not_load_rules(self):
        nlp = medspacy.load(load_rules=False)
        context = nlp.get_pipe("medspacy_context")
        assert not context.rules

    def test_load_lang_model(self):
        # check that spacy pipeline components are still in the nlp object
        nlp = spacy.load("en_core_web_sm", exclude={"ner", "parser", "senter"})
        nlp = medspacy.load(nlp)
        assert {"tagger", "lemmatizer"}.intersection(set(nlp.pipe_names))

    def test_medspacy_tokenizer(self):
        default_tokenizer = spacy.blank("en").tokenizer
        custom_tokenizer = medspacy.load(
            medspacy_enable=["medspacy_tokenizer"]
        ).tokenizer

        text = r"Pt c\o n;v;d h\o chf+cp n/v/d"

        default_doc = default_tokenizer(text)
        medspacy_doc = custom_tokenizer(text)

        assert [token.text for token in default_doc] != [
            token.text for token in medspacy_doc
        ]

        # Check that some expected token boundries are generated
        joined_tokens = " ".join([token.text for token in medspacy_doc])
        assert "c \\ o" in joined_tokens
        assert "n / v / d" in joined_tokens
        assert "chf + cp" in joined_tokens

    def test_disable_medspacy_tokenizer(self):
        default_tokenizer = spacy.blank("en").tokenizer
        custom_tokenizer = medspacy.load(
            medspacy_disable=["medspacy_tokenizer"]
        ).tokenizer

        text = r"Pt c\o n;v;d h\o chf+cp n/v/d"

        default_doc = default_tokenizer(text)
        medspacy_doc = custom_tokenizer(text)

        assert [token.text for token in default_doc] == [
            token.text for token in medspacy_doc
        ]

    def test_medspacy_tokenizer_uppercase(self):
        custom_tokenizer = medspacy.load(
            medspacy_enable=["medspacy_tokenizer"]
        ).tokenizer

        # Issue 13: Ensure that uppercase tokens are not tokenized as each character
        # https://github.com/medspacy/medspacy/issues/13
        text = r"DO NOT BREAK ME UP"

        medspacy_doc = custom_tokenizer(text)

        tokens = [token.text for token in medspacy_doc]

        assert len(tokens) == 5

        # Check that some expected token boundries are generated
        joined_tokens = " ".join(tokens)
        assert "DO NOT BREAK ME UP" in joined_tokens
        assert "B R E A K" not in joined_tokens

    def test_medspacy_tokenizer_numerics(self):
        custom_tokenizer = medspacy.load(
            medspacy_enable=["medspacy_tokenizer"]
        ).tokenizer

        text = r"1.5 mg"

        medspacy_doc = custom_tokenizer(text)

        tokens = [token.text for token in medspacy_doc]

        assert len(tokens) == 2

        # Check that some expected token boundries are generated
        joined_tokens = " ".join(tokens)
        assert "1.5" in joined_tokens
        assert "1 . 5" not in joined_tokens


class TestMedSpaCyForRelease:
    @pytest.mark.parametrize(
        "language_model",
        [
            ("es_core_news_sm"),
            ("pl_core_news_sm"),
            ("de_core_news_sm"),
            ("xx_ent_wiki_sm"),
        ],
    )
    def test_multilingual_load(self, language_model):
        """
        Checks that we can instantiate the pipeline with different language backends
        """
        # Try instantiating the model
        try:
            nlp = medspacy.load(language_model, **{"disable": ["parser"]})
        # Except if you don't have the model downloaded
        except OSError:
            assert True
            return
        doc = nlp(
            "This is a very short piece of text that we want to use for testing. No patients were given type 2 diabetes "
            "as part of this test case. Podczas tego testu nie dano żadnemu pacjentowi cukrzycy typu drugiego."
        )
        assert doc

    def test_pipeline_initiate_with_span_groups(self):
        nlp2 = spacy.blank("en")
        matcher = nlp2.add_pipe(
            "medspacy_target_matcher", config={"result_type": "group"}
        )
        matcher.add(TargetRule("pneumonia", "CONDITION"))
        sectionizer = nlp2.add_pipe(
            "medspacy_sectionizer", config={"input_span_type": "group"}
        )

        doc = nlp2("Past Medical History: Pneumonia, stroke, and cancer")
        assert sectionizer.input_span_type == "group"
        assert len(doc.spans["medspacy_spans"]) > 0
        assert doc.spans["medspacy_spans"][0]._.is_historical is True
