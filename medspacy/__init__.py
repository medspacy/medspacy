from .util import load
from ._version import __version__

from ._extensions import set_extensions, get_extensions, get_doc_extensions, get_span_extensions, get_token_extensions

from . import components

set_extensions()