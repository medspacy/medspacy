from sys import platform

from medspacy.visualization import visualize_ent
import spacy

DEFAULT_PIPENAMES = {
    "sentencizer",
    "target_matcher",
    "context",
    "tokenizer",
}

ALL_PIPE_NAMES = {
    "sentencizer",
    "target_matcher",
    "context",
    "tokenizer",
    "preprocessor",
    "postprocessor",
    "sectionizer",
    "quickumls"
}


def load(model="default", enable=None, disable=None, load_rules=True, quickumls_path = None):
    """Load a spaCy language object with medSpaCy pipeline components.
    By default, the base model will be a blank 'en' model with the
    following components:
        - "tokenizer": A customized tokenizer (set to be nlp.tokenizer)
        - "sentencizer": PyRuSH Sentencizer for sentence splitting
        - "target_matcher": TargetMatcher for extended pattern matching
        - "context": ConText for attribute assertion
    Args:
        model: (str or spaCy Lang model) The base spaCy model to load.
            If 'default', will instantiate from a blank 'en' model.
            Otherwise, if it is a string it will call `spacy.load(model)` along with the enable and disable
                arguments and then add medspaCy pipeline components.
            If it is a spaCy language model, then it will simply add medspaCy components to the existing pipeline.
            Examples:
                >>> nlp = medspacy.load()
                >>> nlp = medspacy.load("en_core_web_sm", disable={"ner"})
                >>> nlp = spacy.load("en_core_web_sm", disable={"ner"}); nlp = medspacy.load(nlp)
        enable (iterable, str, or None): A string or list of component names to include in the pipeline.
            If None, will include all pipeline components listed above.
            If "all", will load all medspaCy components.
            If a list or other iterable, will load the specified pipeline components.
            Note that if using enable, *all* desired pipeline component names must be included.
            Pipeline components could also be instantiated separately and added using the `nlp.add_pipe` method.
            In addition to the default values above, the following medspaCy components may also be added
            and will be added if enable="all":
                - "sectionizer": A SectionDetection component.
                    See medspacy.section_detection.Sectionizer
                - "preprocessor": A wrapper around the tokenizer for destructive preprocessing.
                    Rules added to the preprocessor will modify the underlying text.
                    This component will be set as nlp.tokenizer and will not be listed with nlp.pipe_names.
                    See medspacy.preprocess.Preprocessor
                - "postprocessor": A component for implementing custom business logic at the end of the pipeline
                    and modifying entities by removing them from doc.ents or setting attributes.
                    See medspacy.postprocess.Postprocessor
            Any additional component names (ie., not a medspaCy component) will be passed into
                spacy.load(model_name, enable=enable) and will apply to the base model.
                ie., medspacy.load("en_core_web_sm", enable=["tagger", "parser", "context"])
                will load the tagger and parser from en_core_web_sm and then add context.
        disable (iterable or None): A list of component names to exclude.
            Cannot be set if `enable` is not None.
        load_rules (bool): Whether or not to include default rules for available components.
            If True, sectionizer and context will both be loaded with default rules.
            Default is True.
        quickumls_path (string or None): Path to QuickUMLS resource

    Returns:
        nlp: a spaCy Language object
    """
    enable, disable = _build_pipe_names(enable, disable)
    import spacy
    if isinstance(model, str):
        if model == "default":
            nlp = spacy.blank("en")
        else:
            nlp = spacy.load(model, disable=disable)
    # Check if it is a spaCy model
    elif "spacy.lang" in str(type(model)):
        nlp = model
    else:
        raise ValueError("model must be either 'default', the string name of a spaCy model, or an actual spaCy model. "
                         "You passed in", type(model))

    if "tokenizer" in enable:
        from .custom_tokenizer import create_medspacy_tokenizer
        medspacy_tokenizer = create_medspacy_tokenizer(nlp)
        nlp.tokenizer = medspacy_tokenizer

    if "preprocessor" in enable:
        from .preprocess import Preprocessor
        preprocessor = Preprocessor(nlp.tokenizer)
        nlp.tokenizer = preprocessor


    if "sentencizer" in enable:
        from os import path
        from pathlib import Path

        pyrush_path = path.join(
            Path(__file__).resolve().parents[1], "resources", "rush_rules.tsv"
        )
        from .sentence_splitting import PyRuSHSentencizer

        pyrush = PyRuSHSentencizer(pyrush_path)

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

    if "quickumls" in enable:
        from os import path
        from pathlib import Path

        if quickumls_path is None:
            # let's use a default sample that we provide in medspacy
            # NOTE: Currently QuickUMLS uses an older fork of simstring where databases
            # cannot be shared between Windows and POSIX systems so we distribute the sample for both:

            quickumls_platform_dir = 'QuickUMLS_SAMPLE_lowercase_POSIX_unqlite'
            if platform.startswith("win"):
                quickumls_platform_dir = 'QuickUMLS_SAMPLE_lowercase_Windows_unqlite'

            quickumls_path = path.join(
                Path(__file__).resolve().parents[1], "resources", "quickumls/{0}".format(quickumls_platform_dir)
            )
            print('Loading QuickUMLS resources from a default SAMPLE of UMLS data from here: {}'.format(quickumls_path))

        from quickumls.spacy_component import SpacyQuickUMLS

        quickumls_component = SpacyQuickUMLS(nlp, quickumls_path)
        nlp.add_pipe(quickumls_component)

    if "postprocessor" in enable:
        from .postprocess import Postprocessor
        postprocessor = Postprocessor()
        nlp.add_pipe(postprocessor)

    return nlp


def _build_pipe_names(enable=None, disable=None):
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
            if enable == "all":
                enable = ALL_PIPE_NAMES.copy()
            else:
                enable = {enable}
        else:
            enable = set(enable)
        disable = set(DEFAULT_PIPENAMES).difference(enable)
    else:
        enable = DEFAULT_PIPENAMES
        disable = set()

    return enable, disable
