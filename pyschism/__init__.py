from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from .schism_mesh import *
from .prepare_schism import *
from .split_quad import *