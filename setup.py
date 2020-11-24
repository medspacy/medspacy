from setuptools import setup, find_packages

# read the contents of the README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

def get_version():
    """Load the version from version.py, without importing it.
    This function assumes that the last line in the file contains a variable defining the
    version string with single quotes.
    """
    try:
        with open('medspacy/_version.py', 'r') as f:
            return f.read().split('\n')[0].split('=')[-1].replace('\'', '').strip()
    except IOError:
        raise IOError

setup(
    name="medspacy",
    version=get_version(),
    description="Library for clinical NLP with spaCy.",
    author="medSpaCy",
    author_email="medspacy.dev@gmail.com",
    packages=find_packages(),
    install_requires=[
        # NOTE: spacy imports numpy to bootstrap its own setup.py in 2.3.2
        "spacy>=2.3.0,<=2.3.2",
        "PyRuSH>=1.0.3.5",
        "jsonschema"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_data={"medspacy": ["../resources/*"]},
)
