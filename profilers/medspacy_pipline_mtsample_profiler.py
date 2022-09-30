import re
import cProfile
import pstats
import mechanicalsoup
from mtsample_crawler import mtsample_crawler
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
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
import spacy
from spacy.tokens import Span
import medspacy
from medspacy.preprocess import PreprocessingRule, Preprocessor
from medspacy.ner import TargetRule
from medspacy.context import ConTextRule
from medspacy.section_detection import Sectionizer
from medspacy.postprocess import (
    PostprocessingRule,
    PostprocessingPattern,
    Postprocessor,
)
from medspacy.postprocess import postprocessing_functions

nlp = medspacy.load()
print(nlp.pipe_names)
# pre-processing
preprocessor = Preprocessor(nlp.tokenizer)
nlp.tokenizer = preprocessor
preprocess_rules = [
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
# Target Matcher
Span.set_extension("icd10", default="")
target_matcher = nlp.get_pipe("medspacy_target_matcher")
target_rules = [
    TargetRule(literal="abdominal pain", category="PROBLEM"),
    TargetRule("stroke", "PROBLEM"),
    TargetRule("hemicolectomy", "TREATMENT"),
    TargetRule("Hydrochlorothiazide", "TREATMENT"),
    TargetRule("colon cancer", "PROBLEM"),
    TargetRule("radiotherapy", "PROBLEM", pattern=[{"LOWER": "xrt"}]),
    TargetRule("metastasis", "PROBLEM"),
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
target_matcher.add(target_rules)
# Context
context = nlp.get_pipe("medspacy_context")
context_rules = [
    ConTextRule(
        "diagnosed in <YEAR>",
        "HISTORICAL",
        pattern=[
            {"LOWER": "diagnosed"},
            {"LOWER": "in"},
            {"LOWER": {"REGEX": "^[\d]{4}$"}},
        ],
    )
]
context.add(context_rules)
# Sectionizer
from medspacy.section_detection import SectionRule

sectionizer = nlp.add_pipe("medspacy_sectionizer", config={"rules": "default"})
section_patterns = [SectionRule("Brief Hospital Course:", "hospital_course",)]
sectionizer.add(section_patterns)
# post processing
postprocessor = nlp.add_pipe("medspacy_postprocessor")
postprocess_rules = [
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(
                condition=lambda ent: ent._.section_category == "patient_instructions"
            ),
        ],
        action=postprocessing_functions.remove_ent,
        description="Remove any entities from the instructions section.",
    ),
]
postprocessor.add(postprocess_rules)
print(nlp.pipe_names)
# load 100 mtsamples
docs = mtsample_crawler(num_notes=100)


@profiling(output_file="stat_mtsample/pipeline.prof", sort_by="ncalls", strip_dirs=True)
def fun_profiler():
    for text in docs:
        medspacy_doc = nlp(text)


fun_profiler()
print("FINISH PROFILING!")
