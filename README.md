# medspacy
Library for clinical NLP with spaCy.

![alt text](./images/medspacy_logo.png "medSpaCy logo")



# Overview
MedSpaCy is a library of tools for performing clinical NLP and text processing tasks with the popular [spaCy](spacy.io) 
framework. The `medspacy` package brings together a number of other packages, each of which implements specific 
functionality for common clinical text processing specific to the clinical domain, such as sentence segmentation, 
contextual analysis and attribute assertion, and section detection.

`medspacy` is modularized so that each component can be used independently. All of `medspacy` is designed to be used 
as part of a `spacy` processing pipeline. Each of the following modules is available as part of `medspacy`:
- `medspacy.context`: Implementation of the [ConText](https://www.sciencedirect.com/science/article/pii/S1532046409000744)
for detecting semantic modifiers and attributes of entities, including negation and uncertainty
- `medspacy.ner`: Utilities for extracting concepts from clinical text
- `medspacy.postprocess`: Flexible framework for modifying and removing extracted entities
- `medspacy.preprocess`: Destructive preprocessing for modifying clinical text before processing
- `medspacy.section_detection`: Clinical section detection and segmentation
- `medspacy.sentence_splitter`: Clinical sentence segmentation
- `medspacy.visualization`: Utilities for visualizing concepts and relationships extracted from text

Future work could include I/O, UMLS matching, relations extraction, and pre-trained clinical models.

# Usage
## Installation
You can install `medspacy` using `setup.py`:
```bash
python setup.py install
```

~~Or with pip:~~
```bash
pip install medspacy
```

### Requirements
The following packages are required and installed when `medspacy` is installed:
- spaCy 2.2.2
- Other core medSpaCy packages:
    - [nlp_preprocessor](https://github.com/medspacy/nlp_preprocessor)
    - [pyrush](https://github.com/medspacy/PyRuSH)
    - [target_matcher](https://github.com/medspacy/target_matcher)
    - [sectionizer](https://github.com/medspacy/sectionizer)
    - [cycontext](https://github.com/medspacy/cycontext)
    - [nlp_postprocessor](https://github.com/medspacy/nlp_postprocessor)
    
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
    TargetRule("atrial fibriliation", "PROBLEM"),
    TargetRule("atrial fibrlllation", "PROBLEM", pattern=[{"LOWER": "afib"}]),
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