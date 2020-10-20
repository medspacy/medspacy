from medspacy.visualization import visualize_ent
from IPython.display import HTML, display

DEFAULT_PIPENAMES = {
    "sentencizer",
    "target_matcher",
    "context",
    "tokenizer",
}


def load(model="default", enable=None, disable=None, load_rules=True):
    """Load a spaCy language object with medSpaCy pipeline components.
    By default, the base model will be 'en_core_web_sm' with the
    following components:
        - "tokenizer": A customized tokenizer (set to be nlp.tokenizer)
        - "sentencizer": PyRuSH Sentencizer for sentence splitting
        - "target_matcher": TargetMatcher for extended pattern matching
        - "context": ConText for attribute assertion
    Args:
        model: The name of the base spaCy model to load. Default 'language' will load the tagger and parser
            from "en_core_web_sm".
        enable (iterable or None): A list of component names to include in the pipeline.
            If None, will include all pipeline components listed above.
            Pipeline components could also be instantiated separately and added using the `nlp.add_pipe` method.
            In addition to the default values above, the following components may also be added:
                - "sectionizer": A SectionDetection component
        disable (iterable or None): A list of component names to exclude.
            Cannot be set if `enable` is not None.
        load_rules (bool): Whether or not to include default rules for available components.
            If True, sectionizer and context will both be loaded with default rules.
            Default is True.

    Returns:
        nlp: a spaCy Language object
    """

    model, enable, disable = _build_pipe_names(model, enable, disable)
    import spacy
    nlp = spacy.load(model, disable=disable)

    # Not allowing disabling the tokenizer for now
    if "tokenizer" in enable:
        from .custom_tokenizer import create_medspacy_tokenizer
        medspacy_tokenizer = create_medspacy_tokenizer(nlp)
        nlp.tokenizer = medspacy_tokenizer

    if "sentencizer" in enable:
        from os import path
        from pathlib import Path

        pyrush_path = path.join(
            Path(__file__).resolve().parents[1], "resources", "rush_rules.tsv"
        )
        from .sentence_splitting import PyRuSHSentencizer

        pyrush = PyRuSHSentencizer(pyrush_path)
        if "parser" in nlp.pipe_names:
            if "tagger" in nlp.pipe_names:
                nlp.add_pipe(pyrush, before="tagger")
            else:
                nlp.add_pipe(pyrush, before="parser")
        else:
            nlp.add_pipe(pyrush)

    if "target_matcher" in enable:
        from .ner import TargetMatcher

        target_matcher = TargetMatcher(nlp)
        nlp.add_pipe(target_matcher)

    if "context" in enable:
        from .context import ConTextComponent

        if load_rules:
            context = ConTextComponent(nlp, rules="default")
        else:
            context = ConTextComponent(nlp, rules=None)
        nlp.add_pipe(context)

    if "sectionizer" in enable:
        from .section_detection import Sectionizer

        if load_rules:
            sectionizer = Sectionizer(nlp, patterns="default")
        else:
            sectionizer = Sectionizer(nlp, patterns=None)
        nlp.add_pipe(sectionizer)
    return nlp


def _build_pipe_names(model, enable=None, disable=None):
    """Implement logic based on the pipenames defined in 'enable' and 'disable'.
    If enable and disable are both None, then it will load the default pipenames.
    Otherwise, will allow custom selection of components.
    """
    if enable is not None and disable is not None:
        raise ValueError("Either `enable` or `disable` must be None.")
    if disable is not None:
        # If there's a single pipe name, next it in a set
        if isinstance(disable, str):
            disable = {disable}
        else:
            disable = set(disable)
        enable = DEFAULT_PIPENAMES.difference(set(disable))
    elif enable is not None:
        if isinstance(enable, str):
            enable = {enable}
        else:
            enable = set(enable)
        disable = set(DEFAULT_PIPENAMES).difference(enable)
    else:
        enable = DEFAULT_PIPENAMES
        disable = set()
    # We'll eventually have an actual medSpaCy model here
    # but for now we're basing it off of "en_core_web_sm"
    if model == "default":
        model = "en_core_web_sm"
        disable.update({"ner", "tagger", "parser"})
    return model, enable, disable
