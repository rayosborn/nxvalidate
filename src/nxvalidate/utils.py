import sys

if sys.version_info < (3, 10):
    from importlib_resources import files as package_files
else:
    from importlib.resources import files as package_files

import numpy as np
from dateutil.parser import parse


def is_valid_iso8601(date_string):
    try:
        parse(date_string)
        return True
    except ValueError:
        return False


def is_valid_int(dtype):
    return np.issubdtype(dtype, np.integer) 


def is_valid_float(dtype):
    return np.issubdtype(dtype, np.floating)

# Need type checks for NX_BOOLEAN, NX_CHAR, NX_CHAR_OR_NUMBER, NX_COMPLEX, NX_NUMBER, NX_POSINT, NX_UINT

def load_defaults():
    """ Look up default settings from environment """
    settings = {}
    settings["definitions"] = env_default("NEXUS_DEFINITIONS")
    return settings


def env_default(name, default=None):
    """ Helper function to deal with environment variables """
    result = None
    value = os.getenv(name)
    if value is not None and len(value) > 0:
        result = value
    return result
