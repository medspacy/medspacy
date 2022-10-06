# Overview
[QuickUMLS](https://github.com/Georgetown-IR-Lab/QuickUMLS) is a fast method for extracting UMLS concepts from text.  Our group has worked to make updates to QuickUMLS and some of its methods to ensure that it builds on Windows and works nicely with the other medspaCy components.

# Requirements
On Windows, these instructions require the following:

* conda
* [C++ compiler for Python](https://wiki.python.org/moin/WindowsCompilers)

#Instructions
The following commands must be run after installing medspacy (see [README.md](README.md)).

First, run these with conda, since they do not install easily with pip

```
conda install libiconv nltk unidecode
```

And then these can be run with pip:

```
pip install unqlite>=0.8.1
pip install medspacy_simstring>=2.1
pip install --no-deps medspacy_quickumls==2.6
```

# Testing

After this, the best way to test UMLS extractions is by using the QuickUMLS notebook in this repo.  By default, we package up a small set of SAMPLE concepts from UMLS and make them available as resources.  To generate additional resources from scratch from UMLS, see the instructions at [QuickUMLS](https://github.com/Georgetown-IR-Lab/QuickUMLS).