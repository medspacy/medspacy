# Version 1.1.0

## QuickUMLS
MedspaCy QuickUMLS (v3.0) is now installed by default on Windows! 

Dependencies for this previously were challenging and required both conda and pip.  Now this all installs via pip.  

Tests are updated so that these run on Windows.  

Several areas of documentation have been updated to reflect.  

Huge thanks to Jianlin Shi, and the developers of pysimstring (Luca Soldaini, Perceval Wajsburt, and any others) who made this possible.

## Other
Fixed issues where an exception could be thrown in some components if `set_extension()` was called twice, such as when re-creating a component in a jupyter notebook.

Reverted a default `success_value` to `True` for Postprocessing rules to align with previous versions.

Added `to_json` method to ConText rules.

Prevented spacy v4 or later from being installed.

Fixed some documentation and spelling errors.

# Version 1.0.0

We are calling this release medspacy 1.0.0 because we believe it to be the best stable release so far. It contains a 
large amount of reworking the API in hopes that it will be more stable in the future and a (hopefully) complete 
documentation of all the current features.

Major additions also include serialization with `nlp.pipe` and SpanGroups.

## Documentation

Overhauled medspacy documentation, created docstrings in Google docstring format and type hints for methods. Tutorial 
notebooks all have udpated examples and bug fixes.

## Span Groups

Added functionality using spaCy SpanGroups to all components. Default behavior is to use doc.ents, but span groups can 
be specified and default span group name is "medspacy_spans".

Components that produce entities such as the Target Matcher can specify a destination for the resulting entities as well 
as the name of the span group. Components that consume entities such as Context or the Sectionizer can specify where to 
look for spans, either doc.ents or a span group.

SpanGroups can be enabled in: `TargetMatcher`, `Sectionizer`, `ConText`, `PostProcessor`, `QuickUMLS`, and `DocConsumer`.

## Serialization

Serialization has been enabled across medspacy components. Previously, components and custom objects inside medspacy were
not always JSON-serializable for medspacy's built in multiprocessing. This has been resolved and 
`nlp.pipe([list of texts])` should now work with medspacy components (particularly ConText and Sectionizer) included in
the pipeline.

This helps boost performance by allowing batch processing and multiprocessing.

## Data Protection

Started the process of protecting internal component variables. Previously, the internal structure of medspacy 
components was exposed and could be altered in ways that were not intended. Some variables, such as the internal 
MedspacyMatcher objects and span group information are now stored as private or protected variables with some properties 
allowing limited access.

## Data Simplification

Many internal variables within medspacy contained duplicated or unused information. These have all been removed and some
have been replaced with properties that provide the same information.

## Component Standardization

Components have been standardized across medspaCy.

Components that use the MedspacyMatcher object (TargetMatcher, ConText, Sectionizer), now are initialized with the 
`rules` parameter that can be "default" if there are default rules, None if no rules should be loaded, or a path to a 
JSON file containing the rules.

Components now have an `add()` method that append single rule objects or collections of rule objects to the existing 
rule list.

Components that produce entities, such as QuickUMLS and TargetMatcher, have parameters `result_type` that can be `"ents"`
or `"group"` determining whether SpanGroup functionality is used.

Components that can consume or modify entities have `input_span_type` that can be `"ents"` or `"group"` that determines
where they look for entity spans.

Components with span group functionality all have the span group name determined by `span_group_name`, which by default 
is `"medspacy_spans"`.

We have also renamed `ConTextComponent` to be just `ConText`, so the name is more in line with other medspacy components.

When adding components to a pipeline. The string name of all components is `medspacy_[component_name]`. Abbreviated names 
have been removed.



# Version 0.1.0.1
This release includes a new subpackage `medspacy.io` which includes utilities for converting docs into structured data which can then be written back to a relational database.
## medspacy.io
- `DocConsumer`: A pipeline component which extracts structured data from a doc and stores it in a dictionary which can be accessed through `doc._.get_data()`. Docs processed by `DocConsumer` can then be written to a database or transformed into a pandas database. The following types of data can be extracted from a doc:
    - **"ent"**: The text, label, character offsets, and custom attributes from entities in `doc.ents`: `[("pneumonia", "CONDITION", 5, 15, ...), ...]`
    - **"section"**: Extract the sections of a note: `[("past_medical_history", "PMH: The patient has a hx of..." ...), ...]`
    - **"context"**: Extract entity/modifier pairs extracted by ConText: `[("pneumonia", "no evidence of", "NEGATED_EXISTENCE", ...)]`
    - **"doc"**: Extract the doc text and any specified doc attributes
- `DbConnect` / `DbReader` / `DbWriter`: Utilities for connecting to a database using either sqlite3 or pyodbc, loading texts, and writing back docs processed by `DocConsumer`
- `Pipeline`: A single class which wraps up the `DbReader` and `DbWriter` for processing and saving a series of texts
- `doc._.to_dataframe()`: Convert a doc processed by `DocConsumer` to a pandas DataFrame

# Version 0.1.0.0
This new release includes a lot of new functionality and improvements such as more consistent renaming. 
## Summary
- Support for `QuickUMLS` component for concept extraction and UMLS linking
- Regular expression support in main rule-based components (`TargetMatcher), `ConTextComponent`, and `Sectionizer`)
- New extensions of spaCy `Doc`, `Span`, and `Token` classes
- Refactored rules in for context and section detection
- New notebooks for demonstration

There are some breaking changes to be aware of:
- For ConText, `ConTextItem` has been refactored to `ConTextRule` to define context rules
- For section detection, lists of dictionary patterns have been replaced with lists of `SectionRule` objects to define sectionizer rules
- Renamed section attributes (old -> new):
    - `section_title` -> `section_category`
    - `section_header` -> `section_title`
    - See `notebooks/section_detection` for examples of the new API

##  Details

### Regular expression support
- Added `RegexMatcher` to allow span matching on `Doc` objects using regular expressions
- Created the common `MedspacyMatcher` class to wrap up `Matcher`, `PhraseMatcher`, and `RegexMatcher` functionality
- Updated `ConTextComponent`, `Sectionizer` to use the same API for matching using literal strings, spaCy patterns, or regular expressions
```python
from medspacy.context import ConTextRule
# pattern can now be None, a list of dicts, or a regular expression string
rule = ConTextRule("no history of", "NEGATED_EXISTENCE", pattern=r"no( medical)? history of")
```

### `context`
- Refactored `ConTextItem` to be `ConTextRule` and all relevant attributes to reflect new naming
- Changed the `rule` argument in `ConTextItem` which defines directionality to be `direction`

```python
# Old
from medspacy.context import ConTextItem
ConTextItem("no evidence of", "NEGATED_EXISTENCE", direction="FORWARD") # Will raise exception

# New
from medspacy.context import ConTextRule
ConTextRule("no evidence of", "NEGATED_EXISTENCE", rule="FORWARD")
```

### `section_detection` changes
- Sectionizer now creates sections with three core components. This should help clarify ambiguity between previous naming conventions.
    - `category` the normalized type of the whole section, formerly `section_title`
    - `title` the actual covered text and span matched with the rules, formerly `section_header`
    - `body` the text in between sections, formerly `section_span` or `section_text`
- Sectionizer now uses `SectionRule` rules to define patterns instead of dictionaries
- Sectionizer now stores results in a `Section` class to avoid storing non-serializable elements like spaCy's `Span`. The `Section` object has a variety of properties that can be accessed from `Token`, `Span` and `Doc` levels.
- parenting algorithm works the same but now stores the `Section` of the parent rather than just the name.
- Some sectionizer tests remain commented out. These tests no longer apply to the current API and need some reworking at a later date to develop tests for the same concepts. These mostly have to do with the new method of storing and creating rules, which may involve more sophisticated testing of the MedspacyMatcher in general
- Updated visualizer to reflect use of `Section` objects
- Updated jupyter notebooks with working examples using the adjusted API for `Section` objects.

```python
from medspacy.section_detection import Sectionizer, SectionRule

# Old
sectionizer = Sectionizer(nlp, patterns="default")
pattern = {"section_title": "past_medical_history", "pattern": "past_medical_history"}
sectionizer.add([pattern])
sectionizer(doc)
print(doc._.sections[0]) # namedtuple

# New
sectionizer = Sectionizer(nlp, rules="default")
rule = SectionRule(category="past_medical_history", literal="Past Medical History")
sectionizer.add([rule]) # medspacy.section_detection.section.Section
print(doc._.sections[0]) # medspacy.section_detection.section.Section
```

### `quickumls` changes
- Native support for integration with [QuickUMLS](https://github.com/Georgetown-IR-Lab/QuickUMLS) for concept extraction and UMLS linking.
- Requires some [additional setup for Windows users](windows_and_quickumls.md), as well as for building the resource files.
- We'll add additional documentation throughout, but there is a very simple notebook in the `notebooks/` folder to get you started
- MedspaCy comes with a sample of UMLS resource files, but for the entire UMLS you'll need to download and build the resource files. Will add additional documentation soon.

```python
import medspacy
QUICKUMLS_PATH = "/path/to/umls/resources"

nlp = medspacy.load(enable = {"quickumls"}, 
                    quickumls_path=QUICKUMLS_PATH # Can also be None to load sample
                   )
```

### Extensions
- Declare all custom attributes and methods in `medspacy._extensions`
- Add top-level functions to get extension name and default values:
    - `set_extensions, get_extensions, get_doc_extensions, get_span_extensions, get_token_extensions`
- Add `token._.window(n=2)`, `span._.window(n=2)` functions for getting windows of text around a token or span
- Add `span._.contains(target)` function for searching within a span

```python
from medspacy import get_extensions
print(get_extensions())

doc = nlp("There is no evidence of pneumonia in the image.")
token = doc[3] 
print(token._.window()) # "is no evidence of pneumonia"

span = doc[3:6]
print(span._.window(n=1)) # "no evidence of pneumonia in"
print(span._.contains(r"(pna|pneumonia)")) # True
```
