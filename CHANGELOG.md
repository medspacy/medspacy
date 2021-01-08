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
