from setuptools import setup, find_packages

# read the contents of the README file
import os
from os import path

this_directory = path.abspath(path.dirname(__file__))

long_description = 'Medspacy is a clinical natural language processing toolkit'

# TODO: Fix this later for a richer description
#with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
#    long_description = f.read()

# function to recursively get files for resourcee
def package_files(directory):
    paths = []
    for (p, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join("..", p, filename))
    return paths


# get all files recursively from /resources
resource_files = package_files("./resources")

# get all files recursively from /requirements
resource_files += package_files("./requirements")

# read requirements configuration
with open('requirements/requirements.txt') as f:
    required = f.read().splitlines()


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
    install_requires=required,
    # TODO: Fix this later for a richer description
    #long_description=long_description,
    #long_description_content_type="text/markdown",
    package_data={"medspacy": resource_files},
    python_requires=">=3.8.0",
)
