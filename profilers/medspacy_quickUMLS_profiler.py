import cProfile
import pstats
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
import medspacy
import nltk
from medspacy.util import DEFAULT_PIPENAMES
from medspacy.section_detection import Sectionizer

medspacy_pipes = DEFAULT_PIPENAMES.copy()

if "medspacy_quickumls" not in medspacy_pipes:
    medspacy_pipes.add("medspacy_quickumls")

print(medspacy_pipes)
with open("../notebooks/discharge_summary.txt") as f:
    text = f.read()
nlp = medspacy.load(enable=medspacy_pipes)


@profiling(output_file="stat/quickUMLS.prof", sort_by="ncalls", strip_dirs=True)
def fun_profiler():
    doc = nlp(text)


fun_profiler()
print(nlp.pipe_names)
print("Hello")
