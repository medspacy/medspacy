import pytest

import subprocess
import tempfile
import glob

import medspacy
import spacy

class TestMedSpaCy:
    def test_default_build_pipe_names(self):
        enable, disable = medspacy.util._build_pipe_names(enable=None, disable=None)
        assert enable == {"medspacy_tokenizer", "medspacy_pyrush", "medspacy_target_matcher", "medspacy_context"}
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
        nlp = medspacy.load(enable={"medspacy_target_matcher", "medspacy_sectionizer"})
        assert len(nlp.pipeline) == 2
        assert set(nlp.pipe_names) == {"medspacy_target_matcher", "medspacy_sectionizer"}

    def test_nlp(self):
        nlp = medspacy.load()
        assert nlp("This is a sentence. So is this.")

    def test_load_disable(self):
        nlp = medspacy.load(disable=["context"])
        expected_pipe_names = {
            "medspacy_pyrush",
            "medspacy_target_matcher",
        }
        assert set(nlp.pipe_names) == expected_pipe_names

    def test_load_all_component_names(self):
        expected_pipe_names = {
            "medspacy_pyrush",
            "medspacy_preprocessor",
            "medspacy_tokenizer",
            "medspacy_target_matcher",
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
            "medspacy_context",
            "medspacy_sectionizer",
            "medspacy_postprocessor",
            "medspacy_doc_consumer",
        ]

        nlp = medspacy.load(enable="all")
        assert nlp.pipe_names == full_pipe_names
        assert isinstance(nlp.tokenizer, medspacy.preprocess.Preprocessor)

    # def test_load_sci(self):
    #     # pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.3.0/en_core_sci_sm-0.3.0.tar.gz
    #     assert medspacy.load("en_core_sci_sm")

    def test_execute_example_notebooks(self):

        sample_notebook_files = glob.glob("notebooks/*.txt")

        for sample_notebook_file in sample_notebook_files:
            # Following a pattern from here:
            # https://github.com/ghego/travis_anaconda_jupyter/blob/master/test_nb.py
            with tempfile.NamedTemporaryFile(suffix=".ipynb") as fout:
                args = ["jupyter", "nbconvert", "--to", "notebook", "--execute",
                        "--ExecutePreprocessor.timeout=1000",
                        "--output", fout.name, sample_notebook_file]
                subprocess.check_call(args)

    def test_load_rules(self):
        nlp = medspacy.load(load_rules=True)
        context = nlp.get_pipe("medspacy_context")
        assert context.rules

    def test_not_load_rules(self):
        nlp = medspacy.load(load_rules=False)
        context = nlp.get_pipe("medspacy_context")
        assert not context.rules

    def test_load_lang_model(self):
        nlp = spacy.load("en_core_web_sm", disable={"ner"})
        nlp = medspacy.load(nlp)
        assert {"tagger", "parser"}.intersection(set(nlp.pipe_names))

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
        custom_tokenizer = medspacy.load(enable=['medspacy_tokenizer']).tokenizer

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
        custom_tokenizer = medspacy.load(enable=['medspacy_tokenizer']).tokenizer

        text = r'1.5 mg'

        medspacy_doc = custom_tokenizer(text)

        tokens = [token.text for token in medspacy_doc]

        assert len(tokens) == 2

        # Check that some expected token boundries are generated
        joined_tokens = " ".join(tokens)
        assert "1.5" in joined_tokens
        assert "1 . 5" not in joined_tokens

