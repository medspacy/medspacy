import cProfile
import pstats

# import profiling decorator
from profiling_decorator import profile

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
from medspacy.sentence_splitting import PyRuSHSentencizer

# pipeline is here
nlp = medspacy.load()


@profile(
    output_file="stat/medspacy.custom_tokenizer.create_medspacy_tokenizer.prof",
    sort_by="ncalls",
    strip_dirs=True,
)
def fun_test():
    medspacy_tokenizer = create_medspacy_tokenizer(nlp_blank)


fun_test()
# medspacy.load()
#
# medspacy_tokenizer(text)

print("OKAY!")
