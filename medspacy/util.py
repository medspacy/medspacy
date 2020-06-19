def load(model="default", disable=None):
    if disable is None:
        disable = []

    import spacy

    if model != "default":
        raise NotImplementedError()

    nlp = spacy.load("en_core_web_sm", disable=["ner"])

    if "preprocessor" not in disable:
        from .preprocess import Preprocessor, PreprocessingRule
        preprocessor = Preprocessor(nlp.tokenizer)
        nlp.tokenizer = preprocessor

    if "pyrush" not in disable:
        from os import path
        from pathlib import Path
        pyrush_path = path.join(
            Path(__file__).resolve().parents[1], "resources", "rush_rules.tsv"
        )

        from .sentence_splitter import PyRuSHSentencizer
        pyrush = PyRuSHSentencizer(pyrush_path)
        nlp.add_pipe(pyrush)

    if "target_matcher" not in disable:
        from .ner import TargetMatcher, TargetRule
        target_matcher = TargetMatcher(nlp)
        nlp.add_pipe(target_matcher)

    if "sectionizer" not in disable:
        from .sectionizer import Sectionizer
        sectionizer = Sectionizer(nlp)
        nlp.add_pipe(sectionizer)

    if "context" not in disable:
        from .context import ConTextComponent
        context = ConTextComponent(nlp)
        nlp.add_pipe(context)

    if "postprocessor" not in disable:
        from .postprocess import Postprocessor, PostprocessingRule, PostprocessingPattern
        postprocessor = Postprocessor(debug=True)
        nlp.add_pipe(postprocessor)

    return nlp
