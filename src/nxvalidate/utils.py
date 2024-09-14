import re
import sys

if sys.version_info < (3, 10):
    from importlib_resources import files as package_files
else:
    from importlib.resources import files as package_files

import numpy as np
from dateutil.parser import parse
from nexusformat.nexus.tree import string_dtype


name_pattern = re.compile('^[a-zA-Z0-9_]([a-zA-Z0-9_.]*[a-zA-Z0-9_])?$')


def is_valid_name(name):
    """
    Checks if a given name is valid according to the defined name pattern.

    Parameters
    ----------
    name : str
        The name to be validated.

    Returns
    -------
    bool
        True if the name is valid, False otherwise.
    """
    if re.match(name_pattern, name):
        return True
    else:
        return False


def is_valid_iso8601(date_string):
    """
    Checks if a given date is valid according to the ISO 8601 standard.

    Parameters
    ----------
    date_string : str
        The date string to be validated.

    Returns
    -------
    bool
        True if the date string is valid, False otherwise.
    """
    try:
        parse(date_string)
        return True
    except ValueError:
        return False


def is_valid_int(dtype):
    """
    Checks if a given data type is a valid integer type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid integer type, False otherwise.
    """
    return np.issubdtype(dtype, np.integer) 


def is_valid_float(dtype):
    """
    Checks if a given data type is a valid floating point type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid floating point type, False
        otherwise.
    """
    return np.issubdtype(dtype, np.floating)


def is_valid_bool(dtype):
    """
    Checks if a given data type is a valid boolean type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid boolean type, False otherwise.
    """
    return np.issubdtype(dtype, np.bool_) 


def is_valid_char(dtype):
    """
    Checks if a given data type is a valid character type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid character type, False
        otherwise.
    """
    return (np.issubdtype(dtype, np.str_) or  np.issubdtype(dtype, np.bytes_)
            or dtype == string_dtype)


def is_valid_char_or_number(dtype):
    """
    Checks if a given data type is a valid character or number type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid character or number type, False
        otherwise.
    """
    return is_valid_char(dtype) or is_valid_number(dtype)


def is_valid_complex(dtype):
    """
    Checks if a given data type is a valid complex number type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid complex type, False otherwise.
    """
    return np.issubdtype(dtype, np.complex) 


def is_valid_number(dtype):
    """
    Checks if a given data type is a valid number type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid number type, False otherwise.
    """
    return np.issubdtype(dtype, np.number) 


def is_valid_posint(dtype):
    """
    Checks if a given data type is a valid positive integer type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid positive integer type, False
        otherwise.
    """
    if np.issubdtype(dtype, np.integer):
         info = np.iinfo(dtype)
         return info.max > 0
    return False 


def is_valid_uint(dtype):
    """
    Checks if a given data type is a valid unsigned integer type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid unsigned integer type, False
        otherwise.
    """
    return np.issubdtype(dtype, np.unsignedinteger) 


def strip_namespace(element):
    """
    Recursively strips namespace from an XML element and its children.

    Parameters
    ----------
    element : xml.etree.ElementTree.Element
        The XML element to strip namespace from.
    """    
    if '}' in element.tag:
        element.tag = element.tag.split('}', 1)[1]
    for child in element:
        strip_namespace(child)