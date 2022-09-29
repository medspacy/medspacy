import cProfile
import pstats
from profiling import profiling  # import profiling decorator
import sys

# Set the system path to call medspacy within the repository
sys.path = [
    "/Users/u6022257/opt/anaconda3/lib/python39.zip",
    "/Users/u6022257/opt/anaconda3/lib/python3.9",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/lib-dynload",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/site-packages/aeosa",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/site-packages/medspacy_quickumls-2.3-py3.9.egg",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/site-packages/quickumls_simstring-1.1.5.post1-py3.9-macosx-10.9-x86_64.egg",
    "../",
    "../medspacy",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/site-packages/",
]
# import medspacy from current git repository
import medspacy
import spacy

with open("../notebooks/discharge_summary.txt") as f:
    text = f.read()
nlp_blank = spacy.blank("en")
from medspacy.custom_tokenizer import create_medspacy_tokenizer

# pipeline is here
nlp = medspacy.load(enable=["pyrush"])
medspacy_tokenizer = create_medspacy_tokenizer(nlp_blank)
medspacy_tokenizer(text)
nlp_blank.add_pipe("medspacy_pyrush")
print("nlp from medspacy:", nlp.pipe_names)
print("nlp_blank:", nlp_blank.pipe_names)
# target matcher
from medspacy.ner import TargetMatcher, TargetRule

target_matcher = TargetMatcher(nlp)
target_matcher = nlp.add_pipe("medspacy_target_matcher")
target_rules1 = [
    TargetRule(literal="abdominal pain", category="PROBLEM"),
    TargetRule("stroke", "PROBLEM"),
    TargetRule("hemicolectomy", "TREATMENT"),
    TargetRule("Hydrochlorothiazide", "TREATMENT"),
    TargetRule("colon cancer", "PROBLEM"),
    TargetRule("metastasis", "PROBLEM"),
]
target_matcher.add(target_rules1)
pattern_rules = [
    TargetRule(
        "radiotherapy", "PROBLEM", pattern=[{"LOWER": {"IN": ["xrt", "radiotherapy"]}}]
    ),
    TargetRule(
        "diabetes", "PROBLEM", pattern=r"type (i|ii|1|2|one|two) (dm|diabetes mellitus)"
    ),
]
target_matcher.add(pattern_rules)
from spacy.tokens import Span

Span.set_extension("icd10", default="")
target_rules2 = [
    TargetRule(
        "Type II Diabetes Mellitus",
        "PROBLEM",
        pattern=[
            {"LOWER": "type"},
            {"LOWER": {"IN": ["2", "ii", "two"]}},
            {"LOWER": {"IN": ["dm", "diabetes"]}},
            {"LOWER": "mellitus", "OP": "?"},
        ],
        attributes={"icd10": "E11.9"},
    ),
    TargetRule(
        "Hypertension",
        "PROBLEM",
        pattern=[{"LOWER": {"IN": ["htn", "hypertension"]}}],
        attributes={"icd10": "I10"},
    ),
]
target_matcher.add(target_rules2)
# context
from medspacy.context import ConTextComponent, ConTextRule

context = ConTextComponent(nlp, rules="default")
context = nlp.add_pipe("medspacy_context", config={"rules": "default"})
context_rules = [
    ConTextRule(
        "diagnosed in <YEAR>",
        "HISTORICAL",
        rule="BACKWARD",  # Look "backwards" in the text (to the left)
        pattern=[
            {"LOWER": "diagnosed"},
            {"LOWER": "in"},
            {"LOWER": {"REGEX": "^[\d]{4}$"}},
        ],
    )
]
context.add(context_rules)
# Detect Section
from medspacy.section_detection import Sectionizer

sectionizer = Sectionizer(nlp, rules="default")
sectionizer = nlp.add_pipe("medspacy_sectionizer")
from medspacy.section_detection import SectionRule

section_rules = [
    SectionRule(literal="Brief Hospital Course:", category="hospital_course"),
    SectionRule(
        "Major Surgical or Invasive Procedure:",
        "procedure",
        pattern=r"Major Surgical( or |/)Invasive Procedure:",
    ),
    SectionRule(
        "Assessment/Plan",
        "assessment_and_plan",
        pattern=[
            {"LOWER": "assessment"},
            {"LOWER": {"IN": ["and", "/", "&"]}},
            {"LOWER": "plan"},
        ],
    ),
]
sectionizer.add(section_rules)
# preprocessing
from medspacy.preprocess import Preprocessor, PreprocessingRule
import re

preprocessor = Preprocessor(nlp.tokenizer)
preprocess_rules = [
    lambda x: x.lower(),
    PreprocessingRule(
        re.compile("\[\*\*[\d]{1,4}-[\d]{1,2}(-[\d]{1,2})?\*\*\]"),
        repl="01-01-2010",
        desc="Replace MIMIC date brackets with a generic date.",
    ),
    PreprocessingRule(
        re.compile("\[\*\*[\d]{4}\*\*\]"),
        repl="2010",
        desc="Replace MIMIC year brackets with a generic year.",
    ),
    PreprocessingRule(
        re.compile("dx'd"), repl="Diagnosed", desc="Replace abbreviation"
    ),
    PreprocessingRule(re.compile("tx'd"), repl="Treated", desc="Replace abbreviation"),
    PreprocessingRule(
        re.compile("\[\*\*[^\]]+\]"),
        desc="Remove all other bracketed placeholder text from MIMIC",
    ),
]
preprocessor.add(preprocess_rules)
nlp.tokenizer = preprocessor
# post processing
from medspacy.postprocess import (
    Postprocessor,
    PostprocessingRule,
    PostprocessingPattern,
)
from medspacy.postprocess import postprocessing_functions

postprocessor = Postprocessor(
    nlp, debug=False
)  # Set to True for more verbose information about rule matching
postprocessor = nlp.add_pipe("medspacy_postprocessor")
postprocess_rules = [
    # Instantiate our rule
    PostprocessingRule(
        # Pass in a list of patterns
        patterns=[
            # The pattern will check if the entitie's section is "patient_instructions"
            PostprocessingPattern(
                condition=lambda ent: ent._.section_category == "patient_instructions"
            ),
        ],
        # If all patterns are True, this entity will be removed.
        action=postprocessing_functions.remove_ent,
        description="Remove any entities from the instructions section.",
    ),
]
postprocessor.add(postprocess_rules)


@profiling(output_file="stat/postprocessing.prof", sort_by="ncalls", strip_dirs=True)
def fun_profiler():
    doc = nlp(text)


fun_profiler()
print(nlp.pipe_names)

print("OKAY!")
