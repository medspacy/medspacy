# NLP Postprocessor
This package implements functionality for postprocessing of spaCy entities. It is especially designed to be compatible 
with medSpaCy components such as [cycontext](https://github.com/medspacy/cycontext).
A typical spaCy pipeline processes a Doc with multiple steps of components. For example, an **NER** model might
extract entities and assign labels to spans, and **ConText** will identify contextual modifiers and assign attributes 
like negation and uncertainty. After going through these multiple steps, you may want to implement additional logic 
based on the data collected during processing. You may also want to handle edge cases or very specific logic which is 
not implemented during the processing pipeline. 
The **Postprocessor** offers a way to handle this logic. It is meant to be added as a late or final component in a spaCy
pipeline. It then iterates through the entities in `doc.ents` and runs a number of tests on each entity. Tests which pass
then execute some additional functions which alters or removes the entity.
The high-level API of **Postprocessor** is as follows:
- `Postprocessor`: A component which is added to the NLP pipeline: `nlp.add_pipe(postprocessor)`. This component is 
called on each Doc and iterates through `doc.ents`. The Postprocessor stores a list of `PostprocessingRules`
- `PostprocessingRule`: Contains the logic check against each entity in a Doc and the action to take if the logic 
passes. If a all tests pass, the rule calls an action on an entity such as changing an entity attribute
or removing it. A `PostprocessingRule` contains a list of `PostprocessingPatterns` and an `action` function.
- `PostprocessingPattern`: Defines a single test to be run by a PostprocessingRule. Contains a `condition` function to 
call on an entity. A PostprocessingRule can contain one or more PostprocessingRules.
# Examples

## 1. Remove negated entities
One simple example is removing entities from a Doc which have been negated.
python

```python
doc = nlp("There is no evidence of pneumonia but he does have PE.")
print(doc.ents)
>>> (pneumonia, PE)
import cycontext
context = cycontext.ConTextComponent(nlp, rules="default")
context(doc)
for ent in doc.ents:
    print(ent, ent._.is_negated)
>>> (pneumonia, True)
    (PE, False)

from nlp_postprocessor import Postprocessor, PostprocessingPattern, PostprocessingRule
from nlp_postprocessor.postprocessing_functions import is_negated, remove_ent
postprocessor = Postprocessor()
pattern = PostprocessingPattern(condition=is_negated)
rule = PostprocessingRule(patterns=[pattern], action=remove_ent)
postprocessor.add([rule])

postprocessor(doc)
print(doc.ents)
>>> (PE,)
```

## 2. Word sense disambiguation
In this example, we will take the ambiguous term "ca", which has been extracted as "CANCER",
disambiguate by finding the word "lab" in the sentence, and assigning a new label of "TEST".

```python 
text = "lab results show high level of ca."
doc = nlp(text)
for ent in doc.ents:
    print(ent, ent.label_
>>> (ca, "CANCER")

from nlp_postprocessor.postprocessing_functions import sentence_contains, set_label
postprocessor = Postprocessor()
pattern1 = PostprocessingPattern(condition=lambda ent: ent.text.lower() == "ca")
pattern2 = PostprocessingPattern(condition=is_negated, condition_args=("lab",))
rule = PostprocessingRule(patterns=[pattern1, pattern2], action=set_label, action_args=("TEST",))
postprocessor.add([rule])

postprocessor(doc)
for ent in doc.ents:
    print(ent, ent.label_
>>> (ca, "TEST")
```
