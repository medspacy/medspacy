def register_components():
    """Import each of the custom components and register them with spaCy per v3 requirements."""
    from .target_matcher import TargetMatcher, ConceptTagger
    from .context import ConTextComponent
    from .section_detection import Sectionizer
    from .postprocess import Postprocessor
    from .io import DocConsumer

CUSTOM_PIPELINE_COMPONENTS = (
    # "pyrush_sentencizer",
    "concept_tagger",
    "target_matcher",
    "context",
    "sectionizer",
    "postprocessor",
    "doc_consumer",
)