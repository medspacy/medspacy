import cProfile
from functools import wraps
import sys

sys.path = [
    "/Users/u6022257/opt/anaconda3/lib/python39.zip",
    "/Users/u6022257/opt/anaconda3/lib/python3.9",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/lib-dynload",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/site-packages/aeosa",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/site-packages/medspacy_quickumls-2.3-py3.9.egg",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/site-packages/quickumls_simstring-1.1.5.post1-py3.9-macosx-10.9-x86_64.egg",
    "./",
    "./medspacy",
    "/Users/u6022257/opt/anaconda3/lib/python3.9/site-packages/",
]
print(sys.path)
import medspacy


# profile decorator
def profiling():
    def _profiling(f):
        @wraps(f)
        def __profiling(*rgs, **kwargs):
            pr = cProfile.Profile()
            pr.enable()
            result = f(*rgs, **kwargs)
            pr.disable()
            # save stats into file
            pr.dump_stats("profile_dump")
            return result

        return __profiling

    return _profiling


# load spacy model
nlp = medspacy.load()

# tokenizing and sentence splitting
import spacy

with open("./notebooks/discharge_summary.txt") as f:
    text = f.read()
nlp = spacy.blank("en")
from medspacy.custom_tokenizer import create_medspacy_tokenizer

medspacy_tokenizer = create_medspacy_tokenizer(nlp)
default_tokenizer = nlp.tokenizer
example_text = r"Pt c\o n;v;d h\o chf+cp"
print("Tokens from default tokenizer:")
print(list(default_tokenizer(example_text)))
print("Tokens from medspacy tokenizer:")
print(list(medspacy_tokenizer(example_text)))

print("Hello")
