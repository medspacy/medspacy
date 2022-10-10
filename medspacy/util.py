"""
This module will contain helper functions and classes for common clinical processing tasks
which will be used in many medspaCy components.
"""

from os import path
from pathlib import Path
from sys import platform
from typing import Union, Literal, Iterable, Optional, Set, Tuple

import spacy
from spacy import Language

DEFAULT_PIPE_NAMES = {
    "medspacy_tokenizer",
    "medspacy_pyrush",
    "medspacy_target_matcher",
    "medspacy_context",
}

ALL_PIPE_NAMES = {
    "medspacy_tokenizer",
    "medspacy_preprocessor",
    "medspacy_pyrush",
    "medspacy_target_matcher",
    # "medspacy_quickumls", # quickumls still not included by default due to install issues
    "medspacy_context",
    "medspacy_sectionizer",
    "medspacy_postprocessor",
    "medspacy_doc_consumer",
}


def load(
    model: Union[Literal["default"], str, Language] = "default",
    medspacy_enable: Union[Literal["all", "default"], Iterable[str]] = "default",
    medspacy_disable: Optional[Iterable[str]] = None,
    load_rules: bool = True,
    quickumls_path: Optional[str] = None,
    **model_kwargs,
):
    """Load a spaCy language object with medSpaCy pipeline components.
    By default, the base model will be a blank 'en' model with the
    following components:
        - "medspacy_tokenizer": A customized, more aggressive tokenizer than the default spaCy tokenizer. This is set to
            `nlp.tokenizer` and is not loaded as a pipeline component.
        - "medspacy_pyrush": PyRuSH Sentencizer for sentence splitting
        - "medspacy_target_matcher": TargetMatcher for extended pattern matching
        - "medspacy_context": ConText for attribute assertion
    Args:
        model: The base spaCy model to load. If 'default', will instantiate from a blank 'en' model. If it is a spaCy
            language model, then it will simply add medspaCy components to the existing pipeline. If it is a string
            other than 'default', passes the string to spacy.load(model, **model_kwargs).
        medspacy_enable: Specifies which components to enable in the medspacy pipeline. If "default", will load all components
            found in `DEFAULT_PIPE_NAMES`. These represent the simplest components used in a clinical NLP pipeline:
            tokenization, sentence detection, concept identification, and ConText. If "all", all components in medspaCy
            will be loaded. If a collection of strings, the components specified will be loaded.
        medspacy_disable: A collection of component names to exclude. Requires "all" is the value for `enable`.
        load_rules: Whether to include default rules for available components. If True, sectionizer and context will
            both be loaded with default rules. Default is True.
        quickumls_path: Path to QuickUMLS dictionaries if it is included in the pipeline.
        model_kwargs: Optional model keyword arguments to pass to spacy.load().

    Returns:
        A spaCy Language object containing the specified medspacy components.
    """

    medspacy_enable, medspacy_disable = _build_pipe_names(
        medspacy_enable, medspacy_disable
    )

    if model == "default":
        nlp = spacy.blank("en")
    elif isinstance(model, Language):
        nlp = model
    elif isinstance(model, str):
        nlp = spacy.load(model, **model_kwargs)
    else:
        raise ValueError(
            "model must be either 'default' or an actual spaCy Language object, not ",
            type(model),
        )

    if "medspacy_tokenizer" in medspacy_enable:
        from .custom_tokenizer import create_medspacy_tokenizer

        medspacy_tokenizer = create_medspacy_tokenizer(nlp)
        nlp.tokenizer = medspacy_tokenizer

    if "medspacy_preprocessor" in medspacy_enable:
        from .preprocess import Preprocessor

        preprocessor = Preprocessor(nlp.tokenizer)
        nlp.tokenizer = preprocessor

    if "medspacy_pyrush" in medspacy_enable:
        pyrush_path = path.join(
            Path(__file__).resolve().parents[1], "resources", "rush_rules.tsv"
        )
        nlp.add_pipe("medspacy_pyrush", config={"rules_path": pyrush_path})

    if "medspacy_target_matcher" in medspacy_enable:
        nlp.add_pipe("medspacy_target_matcher")

    if "medspacy_quickumls" in medspacy_enable:
        # NOTE: This could fail if a user requests this and QuickUMLS cannot be found
        # but if it's requested at this point, let's load it

        # let's see if we need to supply a path for QuickUMLS.  If none is provided,
        # let's point to the demo data
        if quickumls_path is None:
            quickumls_path = get_quickumls_demo_dir()

            print(
                "Loading QuickUMLS resources from a Medspacy-distributed SAMPLE of UMLS data from here: {}".format(
                    quickumls_path
                )
            )

        nlp.add_pipe("medspacy_quickumls", config={"quickumls_fp": quickumls_path})

    if "medspacy_context" in medspacy_enable:
        if load_rules is True:
            config = {}
        else:
            config = {"rules": None}
        nlp.add_pipe("medspacy_context", config=config)

    if "medspacy_sectionizer" in medspacy_enable:
        if load_rules is True:
            config = {}
        else:
            config = {"rules": None}
        nlp.add_pipe("medspacy_sectionizer", config=config)

    if "medspacy_postprocessor" in medspacy_enable:
        nlp.add_pipe("medspacy_postprocessor")

    if "medspacy_doc_consumer" in medspacy_enable:
        nlp.add_pipe("medspacy_doc_consumer")

    return nlp


def _build_pipe_names(
    enable: Union[str, Iterable[str]], disable: Optional[Iterable[str]] = None
) -> Tuple[Set[str], Set[str]]:
    """
    Implement logic based on the pipenames defined in 'enable' and 'disable'. If enable and disable are both None,
    then it will load the default pipenames. Otherwise, will allow custom selection of components.

    Args:
        enable: "all" loads components from ALL_PIPE_NAMES. "default" loads components from DEFAULT_PIPE_NAMES.
            Otherwise, loads he list of components as components.
        disable: The optional list of components to disable. Set difference of enable.

    Returns:
        A complete list of enabled and disabled components, with all components listed and empty intersection.
    """
    if not enable:
        raise ValueError(
            "Enable cannot be none, please specify 'all', 'default' or a list of components."
        )

    # cannot allow lists of enabled and disabled components, what happens if "context" is both enabled and disabled?
    if (not isinstance(enable, str) and isinstance(enable, Iterable)) and isinstance(
        disable, Iterable
    ):
        raise ValueError("Both enable and disable cannot be collections of components.")

    # set which components are enabled first
    if enable == "all":
        enable = ALL_PIPE_NAMES
    elif enable == "default":
        enable = DEFAULT_PIPE_NAMES
    else:
        enable = set(enable)

    # then find the difference with deactivated components
    if disable is not None:
        enable = enable.difference(set(disable))
    else:
        disable = set()  # otherwise disable is empty

    return enable, disable


def tuple_overlaps(a: Tuple[int, int], b: Tuple[int, int]):
    """
    Calculates whether two tuples overlap. Assumes tuples are sorted to be like spans (start, end)

    Args:
        a: A tuple representing a span (start, end).
        b: A tuple representing a span (start, end).

    Returns:
        Whether the tuples overlap.
    """
    return a[0] <= b[0] < a[1] or a[0] < b[1] <= a[1]


def get_quickumls_demo_dir():
    # let's use a default sample that we provide in medspacy
    # NOTE: Currently QuickUMLS uses an older fork of simstring where databases
    # cannot be shared between Windows and POSIX systems so we distribute the sample for both:

    quickumls_platform_dir = "QuickUMLS_SAMPLE_lowercase_POSIX_unqlite"
    if platform.startswith("win"):
        quickumls_platform_dir = "QuickUMLS_SAMPLE_lowercase_Windows_unqlite"

    quickumls_path = path.join(
        Path(__file__).resolve().parents[1],
        "resources",
        "quickumls/{0}".format(quickumls_platform_dir),
    )

    return quickumls_path
