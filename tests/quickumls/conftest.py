import spacy
import pytest
from medspacy.util import get_quickumls_demo_dir


@pytest.fixture(scope="session")
def quickumls_nlp():
    """Session-scoped QuickUMLS pipeline shared across all quickumls tests.

    Only one QuickUMLS instance can reliably use the simstring database
    per process, so all tests must share this single pipeline.
    """
    _nlp = spacy.blank("en")
    _nlp.add_pipe(
        "medspacy_quickumls",
        config={
            "threshold": 0.7,
            "best_match": False,
            "quickumls_fp": get_quickumls_demo_dir("en"),
        },
    )
    return _nlp
