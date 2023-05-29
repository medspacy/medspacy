import os
# use this to satisfy toml dynamic version configure without import othere dependencies
__version__ = open(os.path.join(os.path.dirname(__file__), 'VERSION')).read()
