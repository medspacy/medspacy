from setuptools import setup, find_namespace_packages

# read the contents of the README file
import os
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()
    
# function to recursively get files for resourcee
def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths
    
# get all files recursively from /resources
resource_files = package_files('./resources')

setup(
    name="medspacy",
    version="0.0.1.1",
    description="Library for clinical NLP with spaCy.",
    author="medSpaCy",
    author_email="medspacy.dev@gmail.com",
    packages=["medspacy"],
    install_requires=[
        "spacy>=2.2.2,<2.3",
        "nlp_preprocessor>=0.0.1",
        "PyRuSH>=1.0.3.5",
        "cycontext>=1.0.3.1",
        "clinical_sectionizer>=0.1.1",
        "target_matcher>=0.0.3",
        "nlp_postprocessor>=0.0.1",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_data={"medspacy": resource_files},
)
