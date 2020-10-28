from medspacy.visualization import visualize_ent

DEFAULT_PIPENAMES = {
    "tagger",
    "parser",
    "preprocessor",
    "sentencizer",
    "context",
    "target_matcher",
    "sectionizer",
    "postprocessor",
}


def load(model="default", enable=None, disable=None, load_rules=True, quickumls_path = None):
    """Load a spaCy language object with medSpaCy pipeline components.
    By default, the base model will be 'en_core_web_sm' with the 'tagger'
    and 'parser' pipeline components, followed by the following medSpaCy
    components:
        - preprocessor (set to be nlp.tokenizer)
        - sentencizer
        - target_matcher
        - sectionizer
        - context
        - postprocessor

    Args:
        model: The name of the base spaCy model to load. Default 'language' will load the tagger and parser
            from "en_core_web_sm".
        enable (iterable or None): A list of component names to include in the pipeline.
        If None, will include all pipeline components listed above.
        disable (iterable or None): A list of component names to exclude.
            Cannot be set if `enable` is not None.
        load_rules (bool): Whether or not to include default rules for available components.
            If True, sectionizer and context will both be loaded with default rules.
            Default is True.
        quickumls_path (string or None): Path to QuickUMLS resource

    Returns:
        nlp: a spaCy Language object
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
    if model == "default":
        model = "en_core_web_sm"
        disable.add("ner")

    import spacy

    nlp = spacy.load(model, disable=disable)

    if "preprocessor" in enable:
        from .preprocess import Preprocessor

        preprocessor = Preprocessor(nlp.tokenizer)
        nlp.tokenizer = preprocessor
        
    if "tokenizer" in enable:
        from .custom_tokenizer import create_medspacy_tokenizer
        
        tokenizer = create_medspacy_tokenizer(nlp)
        nlp.tokenizer = tokenizer

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

    if "sectionizer" in enable:
        from .section_detection import Sectionizer

        if load_rules:
            sectionizer = Sectionizer(nlp, patterns="default")
        else:
            sectionizer = Sectionizer(nlp, patterns=None)
        nlp.add_pipe(sectionizer)
        
    if "quickumls" in enable:
        from os import path
        from pathlib import Path
        
        if quickumls_path is None:
            # let's use a default sample that we provide in medspacy...
            quickumls_path = path.join(
                Path(__file__).resolve().parents[1], "resources", "quickumls/QuickUMLS_SAMPLE_lowercase_unqlite"
            )
            print('Loading QuickUMLS resources from a default SAMPLE of UMLS data from here: {}'.format(quickumls_path))
            
        from quickumls.spacy_component import SpacyQuickUMLS
        
        quickumls_component = SpacyQuickUMLS(nlp, quickumls_path)
        nlp.add_pipe(quickumls_component)

    if "context" in enable:
        from .context import ConTextComponent

        if load_rules:
            context = ConTextComponent(nlp, rules="default")
        else:
            context = ConTextComponent(nlp, rules=None)
        nlp.add_pipe(context)

    if "postprocessor" in enable:
        from .postprocess import Postprocessor

        postprocessor = Postprocessor()
        nlp.add_pipe(postprocessor)

    return nlp