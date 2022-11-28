from setuptools import setup, find_packages
from sys import platform

# read the contents of the README file
import os
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

additional_installs = []
if platform.startswith("win"):
    print(
        "Not installing QuickUMLS for Windows since it currently requires conda (as opposed to just pip)"
    )
else:
    # Using a trick from StackOverflow to set an impossibly high version number
    # to force getting latest from GitHub as opposed to PyPi
    # since QuickUMLS has not made a release with some recent MedSpacy contributions...
    quickumls_package = "medspacy_quickumls==2.7"
    additional_installs.append(quickumls_package)
    print("Attempting to install quickumls package: {}".format(quickumls_package))

# function to recursively get files for resourcee
def package_files(directory):
    paths = []
    for (p, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join("..", p, filename))
    return paths


# get all files recursively from /resources
resource_files = package_files("./resources")


def get_version():
    """Load the version from version.py, without importing it.
    This function assumes that the last line in the file contains a variable defining the
    version string with single quotes.
    """
    try:
        with open("medspacy/_version.py", "r") as f:
            version_value = f.read().split("\n")[0].split("=")[-1].strip()
            
            # remove either double-quotes or single-quotes
            version_value = version_value.replace("'", "")
            version_value = version_value.replace('"', "")
            
            #print(f'version value verbatim: {version_value}')
            
            return version_value
    except IOError:
        raise IOError


setup(
    name="medspacy",
    version=get_version(),
    description="Library for clinical NLP with spaCy.",
    author="medSpaCy",
    packages=find_packages(),
    install_requires=[
        "spacy>=3.4.1",
        "PyRuSH>=1.0.8",
        "pysbd==0.3.4",
        "jsonschema",
    ]
    + additional_installs,
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_data={"medspacy": resource_files},
    python_requires=">=3.8.0",
)
