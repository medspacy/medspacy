import os, sys
# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())

import inspect
import types
import warnings

# quickumls is an optional heavy dependency. It is not installed in minimal
# environments, but medspacy/__init__ imports medspacy.util which imports it at
# module level. Stub it so these tests run hermetically (no network / installs).
_quickumls_stub = types.ModuleType("quickumls")
_quickumls_stub.spacy_component = object()
sys.modules.setdefault("quickumls", _quickumls_stub)

import spacy
import pytest

import medspacy  # noqa: F401  (registers medspacy extensions)
from medspacy._extensions import get_data
from medspacy.section_detection import Sectionizer, SectionRule
from medspacy.target_matcher import TargetMatcher, TargetRule
from spacy.tokens import Span

HERE = os.path.realpath(__file__)


def _assert_warns_at_caller(caught, expected_lineno, message_part):
    """Assert exactly one matching warning, attributed to the caller's line."""
    matching = [w for w in caught if message_part in str(w.message)]
    assert len(matching) == 1, (
        f"expected 1 warning containing {message_part!r}, got {len(matching)}"
    )
    w = matching[0]
    assert os.path.realpath(w.filename) == HERE, (
        f"warning points at {w.filename}:{w.lineno} instead of the caller "
        f"({HERE}:{expected_lineno}); stacklevel is missing or wrong"
    )
    assert w.lineno == expected_lineno, (
        f"warning lineno {w.lineno} != caller line {expected_lineno}"
    )


@pytest.fixture(scope="module")
def nlp():
    return spacy.blank("en")


class TestWarningStacklevel:
    """Regression tests for medspacy#336: warnings must point at user code."""

    def test_sectionizer_duplicate_title_warning(self, nlp):
        sectionizer = Sectionizer(nlp, rules=None)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            expected_lineno = inspect.currentframe().f_lineno + 1
            sectionizer.add(
                [
                    SectionRule(
                        literal="History of Present Illness:",
                        category="hpi",
                        parents=["a"],
                    ),
                    SectionRule(
                        literal="History of Present Illness:",
                        category="hpi",
                        parents=["b"],
                    ),
                ]
            )
        _assert_warns_at_caller(caught, expected_lineno, "Merging parents")

    def test_sectionizer_parent_required_warning(self, nlp):
        sectionizer = Sectionizer(nlp, rules=None)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            expected_lineno = inspect.currentframe().f_lineno + 1
            sectionizer.add(
                [
                    SectionRule(
                        literal="Assessment:",
                        category="assess",
                        parents=["a"],
                        parent_required=True,
                    ),
                    SectionRule(
                        literal="Assessment:",
                        category="assess",
                        parent_required=False,
                    ),
                ]
            )
        _assert_warns_at_caller(
            caught, expected_lineno, "different parent_required option"
        )

    def test_target_matcher_entity_conflict_warning(self, nlp):
        target_matcher = TargetMatcher(nlp, rules=None, result_type="ents")
        target_matcher.add([TargetRule(literal="fever", category="CONDITION")])
        doc = nlp("patient has fever")
        # Pre-existing entity the matcher result will conflict with. Must be
        # labeled: spaCy silently drops unlabeled spans from doc.ents.
        doc.ents = (Span(doc, 2, 3, label="CONDITION"),)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            expected_lineno = inspect.currentframe().f_lineno + 1
            target_matcher(doc)
        # NOTE: spaCy's own [W036] (empty token Matcher inside
        # MedspacyMatcher) also fires; it is unrelated to #336 and filtered
        # out here by matching on the medspacy warning text.
        _assert_warns_at_caller(
            caught, expected_lineno, "conflicts with a pre-existing entity"
        )

    def test_get_data_none_warning(self, nlp):
        doc = nlp("plain text")
        assert doc._.data is None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            expected_lineno = inspect.currentframe().f_lineno + 1
            get_data(doc)
        _assert_warns_at_caller(caught, expected_lineno, "doc._.data is None")
