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
import medspacy
from medspacy.ner import TargetRule

texts = [
    "Family History: Mother with stroke at age 82.",
    "Past Medical History: colon cancer",
    "Allergies: Hydrochlorothiazide",
    "Some metastasis.",
    "Patient presents for radiotherapy to treat her breast cancer.",
]
# nlp = medspacy.load(enable=["pyrush"])

# nlp = medspacy.load(enable=["pyrush", "target_matcher", "context", "sectionizer"])
# print(nlp.pipe_names)
