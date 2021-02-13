from setuptools import setup, find_packages
from sys import platform

# read the contents of the README file
import os
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

additional_installs = []
if platform.startswith('win'):
    print('Not installing QuickUMLS for Windows since it currently requires conda (as opposed to just pip)')
else:
    # Using a trick from StackOverflow to set an impossibly high version number
    # to force getting latest from GitHub as opposed to PyPi
    # since QuickUMLS has not made a release with some recent MedSpacy contributions...
    quickumls_package = 'medspacy_quickumls>=2.4.1'
    additional_installs.append(quickumls_package)
    print('Attempting to install quickumls package: {}'.format(quickumls_package))

# function to recursively get files for resourcee
def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


# get all files recursively from /resources
resource_files = package_files('./resources')

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
        "spacy>=3.0.1",
        "PyRuSH>=1.0.3.5",
        "jsonschema"
    ] + additional_installs,
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_data={"medspacy": resource_files},
)
