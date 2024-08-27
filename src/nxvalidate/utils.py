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

def is_valid_bool(dtype):
    return np.issubdtype(dtype, np.bool_) 

def is_valid_char(dtype):
    return np.issubdtype(dtype, np.str_) or  np.issubdtype(dtype, np.bytes_)

def is_valid_char_or_number(dtype):
    return np.issubdtype(dtype, np.number) or np.issubdtype(dtype, np.str_) 

def is_valid_complex(dtype):
    return np.issubdtype(dtype, np.complex) 

def is_valid_number(dtype):
    return np.issubdtype(dtype, np.number) 

def is_valid_posint(dtype):
    if np.issubdtype(dtype, np.integer):
         info = np.iinfo(dtype)
         return info.max > 0
    return False 

def is_valid_uint(dtype):
    return np.issubdtype(dtype, np.unsignedinteger) 


def strip_namespace(element):
    if '}' in element.tag:
        element.tag = element.tag.split('}', 1)[1]
    for child in element:
        strip_namespace(child)