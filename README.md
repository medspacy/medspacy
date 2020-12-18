[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Build Status](https://github.com/medspacy/medspacy/workflows/medspacy/badge.svg)

# medspacy
Library for clinical NLP with spaCy. 

![alt text](./images/medspacy_logo.png "medSpaCy logo")

**MedSpaCy is currently in beta.**


# Overview
MedSpaCy is a library of tools for performing clinical NLP and text processing tasks with the popular [spaCy](spacy.io) 
framework. The `medspacy` package brings together a number of other packages, each of which implements specific 
functionality for common clinical text processing specific to the clinical domain, such as sentence segmentation, 
contextual analysis and attribute assertion, and section detection.

`medspacy` is modularized so that each component can be used independently. All of `medspacy` is designed to be used 
as part of a `spacy` processing pipeline. Each of the following modules is available as part of `medspacy`:
- `medspacy.preprocess`: Destructive preprocessing for modifying clinical text before processing
- `medspacy.sentence_splitter`: Clinical sentence segmentation
- `medspacy.ner`: Utilities for extracting concepts from clinical text
- `medspacy.context`: Implementation of the [ConText](https://www.sciencedirect.com/science/article/pii/S1532046409000744)
for detecting semantic modifiers and attributes of entities, including negation and uncertainty
- `medspacy.section_detection`: Clinical section detection and segmentation
- `medspacy.postprocess`: Flexible framework for modifying and removing extracted entities
- `medspacy.visualization`: Utilities for visualizing concepts and relationships extracted from text
- `SpacyQuickUMLS`: UMLS concept extraction compatible with spacy and medspacy implemented by [QuickUMLS]
	- NOTE: This component is installed by default on MacOS and Linux but not Windows.  For more defails and Windows installation: [QuickUMLS on Windows](windows_and_quickumls.md)

Future work could include I/O, relations extraction, and pre-trained clinical models.

# Usage
## Installation
You can install `medspacy` using `setup.py`:
```bash
python setup.py install
```

Or with pip:
```bash
pip install medspacy
```

If you download other models, you can use them by providing the model itself or model name to `medspacy.load(model_name)`:
```python
import spacy; import medspacy
# Option 1: Load default
nlp = medspacy.load()

# Option 2: Load from existing model
nlp = spacy.load("en_core_web_sm", disable={"ner"})
nlp = medspacy.load(nlp)

# Option 3: Load from model name
nlp = medspacy.load("en_core_web_sm", disable={"ner"})
```

### Requirements
The following packages are required and installed when `medspacy` is installed:
- spaCy 2.3
- [pyrush](https://github.com/medspacy/PyRuSH)
    
## Basic Usage
Here is a simple example showing how to implement and visualize a simple rule-based pipeline using `medspacy`:
```python
import medspacy
from medspacy.ner import TargetRule
from medspacy.visualization import visualize_ent

# Load medspacy model
nlp = medspacy.load()

text = """
Past Medical History:
1. Atrial fibrillation
2. Type II Diabetes Mellitus

Assessment and Plan:
There is no evidence of pneumonia. Continue warfarin for Afib. Follow up for management of type 2 DM.
"""

# Add rules for target concept extraction
target_matcher = nlp.get_pipe("target_matcher")
target_rules = [
    TargetRule("atrial fibrillation", "PROBLEM"),
    TargetRule("atrial fibrillation", "PROBLEM", pattern=[{"LOWER": "afib"}]),
    TargetRule("pneumonia", "PROBLEM"),
    TargetRule("Type II Diabetes Mellitus", "PROBLEM", 
              pattern=[
                  {"LOWER": "type"},
                  {"LOWER": {"IN": ["2", "ii", "two"]}},
                  {"LOWER": {"IN": ["dm", "diabetes"]}},
                  {"LOWER": "mellitus", "OP": "?"}
              ]),
    TargetRule("warfarin", "MEDICATION")
]
target_matcher.add(target_rules)

doc = nlp(text)
visualize_ent(doc)
```

`Output:`
![alt text](./images/simple_text_visualization.png "Example of clinical text processed by medSpaCy")

For more detailed examples and explanations of each component, see the [notebooks](./notebooks) folder.

# Made with medSpaCy
Here are some links to projects or tutorials which use medSpacy. If you have a project which uses medSpaCy which you'd like to use, let us know!
- [VA_COVID-19_NLP_BSV](https://github.com/abchapman93/VA_COVID-19_NLP_BSV): An NLP pipeline for identifying positive cases of COVID-19 from clinical text. Deployed as part of the Department of Veterans Affairs response to COVID-19
- [clinspacy](https://ml4lhs.github.io/clinspacy/index.html): An R wrapper for spaCy, sciSpaCy, and medSpaCy for performing clinical NLP and UMLS linking in R
- [mimic34md2020_materials](https://github.com/Melbourne-BMDS/mimic34md2020_materials): A crash course in clinical data science from the University of Melbourne. For medSpaCy materials, see `notebooks/nlp-*.ipynb`
