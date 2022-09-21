import cProfile
import pstats
import sys

# Set the system path to call medspacy within the repository
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
# import medspacy from current git repository
import medspacy

print(sys.path)


def profiler_shell(func):
    pr = cProfile.Profile()
    pr.enable()
    func
    pr.disable()
    stats = pstats.Stats(pr).sort_stats("ncalls")
    stats.strip_dirs()  # remove the dir names
    stats.print_stats()


text = """
 Past Medical History:
 1. Atrial fibrillation
 2. Type II Diabetes Mellitus
 Assessment and Plan:
 There is no evidence of pneumonia. Continue warfarin for Afib. Follow up for management of type 2 DM.
 """
import spacy

with open("./notebooks/discharge_summary.txt") as f:
    text = f.read()
nlp_blank = spacy.blank("en")
from medspacy.custom_tokenizer import create_medspacy_tokenizer
from medspacy.sentence_splitting import PyRuSHSentencizer

# medspacy_tokenizer = create_medspacy_tokenizer(nlp_blank)

# test medspacy.util.load()
profiler = cProfile.Profile()
profiler.enable()
medspacy.load()
medspacy_tokenizer = create_medspacy_tokenizer(nlp_blank)
medspacy_tokenizer(text)
profiler.disable()
stats = pstats.Stats(profiler).sort_stats("ncalls")
stats.strip_dirs()  # remove the dir names
stats.print_stats()
# stats.dump_stats(filename)
#%load_ext snakeviz #this can only used in ipython
#%snakeviz medspacy.load()
print("OKAY!")
