from spacy.language import Language
from sys import platform


@Language.factory("medspacy_quickumls")
def create_quickumls(nlp, name="medspacy_quickumls", quickumls_path=None):
    from os import path
    from pathlib import Path

    if quickumls_path is None:
        # let's use a default sample that we provide in medspacy
        # NOTE: Currently QuickUMLS uses an older fork of simstring where databases
        # cannot be shared between Windows and POSIX systems so we distribute the sample for both:

        quickumls_platform_dir = "QuickUMLS_SAMPLE_lowercase_POSIX_unqlite"
        if platform.startswith("win"):
            quickumls_platform_dir = "QuickUMLS_SAMPLE_lowercase_Windows_unqlite"

        quickumls_path = path.join(
            Path(__file__).resolve().parents[1], "resources", "quickumls/{0}".format(quickumls_platform_dir)
        )
        print("Loading QuickUMLS resources from a default SAMPLE of UMLS data from here: {}".format(quickumls_path))

    from quickumls.spacy_component import SpacyQuickUMLS

    quickumls_component = SpacyQuickUMLS(nlp, quickumls_path)

    return quickumls_component
