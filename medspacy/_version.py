import os
# use this to satisfy toml version configure without import dependencies
__version__ = open(os.path.join(os.path.dirname(__file__), 'VERSION')).read()
