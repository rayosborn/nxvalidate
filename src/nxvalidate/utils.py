# -----------------------------------------------------------------------------
# Copyright (c) 2024, Kaitlyn Marlor, Ray Osborn, Justin Wozniak.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------
import logging
import os
import re
import sys

if sys.version_info < (3, 10):
    from importlib_resources import package_files
else:
    from importlib.resources import package_files

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


def convert_xml_dict(xml_dict):
    """
    Convert an XML dictionary to a more readable format.

    Parameters
    ----------
    xml_dict : dict
        The XML dictionary to be converted.

    Returns
    -------
    dict
        The converted XML dictionary.

    Notes
    -----
    If the XML dictionary contains '@type' and '@name', it will be
    converted to a dictionary with '@name' as the key. If the XML
    dictionary contains only '@type', it will be converted to a
    dictionary with '@type' as the key. If the XML dictionary does not
    contain '@type' or '@name', it will be returned as is.
    """
    if '@type' in xml_dict:
        if '@name' in xml_dict:
            key = '@name'
        else:
            key = '@type'
    elif '@name' in xml_dict:
        key = '@name'
    else:
        return xml_dict
    return {xml_dict[key]: {k: v for k, v in xml_dict.items() if k != key}}


def xml_to_dict(element):
    """
    Convert an XML element to a dictionary.

    Parameters
    ----------
    element : xml element
        The XML element to be converted.

    Returns
    -------
    dict
        A dictionary representation of the XML element.
    """
    result = {}

    if element.attrib:
        attrs = element.attrib
        for attr in attrs:
            result[f"@{attr}"] = attrs[attr]

    for child in element:
        if child.tag == 'doc':
            continue
        elif child.tag == 'enumeration':
            result[child.tag] = [item.attrib['value'] for item in child]
        elif child.tag == 'dimensions':
            result[child.tag] =  {}
            if 'rank' in child.attrib:
                result[child.tag].update({'rank': child.attrib['rank']})
            result[child.tag]['dim'] = {}
            for item in [c for c in child if c.tag == 'dim']:
                if 'index' in item.attrib and 'value' in item.attrib:
                    result[child.tag]['dim'].update(
                        {int(item.attrib['index']): item.attrib['value']})
        else:
            child_dict = convert_xml_dict(xml_to_dict(child))       
            if child.tag in result:
                result[child.tag].update(child_dict)
            else:
                result[child.tag] = child_dict

    return result

def merge_dicts(dict1, dict2):
    """
    Recursively merges two dictionaries into one.

    Parameters
    ----------
    dict1 : dict
        The dictionary to be updated.
    dict2 : dict
        The dictionary to update with.

    Returns
    -------
    dict
        The updated dictionary.
    """
    for key, value in dict2.items():
        if (key in dict1 and isinstance(dict1[key], dict)
                and isinstance(value, dict)):
            merge_dicts(dict1[key], value)
        else:
            dict1[key] = value
    return dict1

def readaxes(axes):
    """Return a list of axis names stored in the 'axes' attribute.

    If the input argument is a string, the names are assumed to be separated
    by a delimiter, which can be white space, a comma, or a colon. If it is
    a list of strings, they are converted to strings.

    Parameters
    ----------
    axes : str or list of str
        Value of 'axes' attribute defining the plotting axes.

    Returns
    -------
    list of str
        Names of the axis fields.
    """
    if isinstance(axes, str):
        return list(re.split(r'[,:; ]',
                    str(axes).strip('[]()').replace('][', ':')))
    else:
        return [str(axis) for axis in axes]


def match_strings(pattern_string, target_string):
    # Create regular expression patterns for both cases
    """
    Check if a target string matches a given pattern string, allowing for
    uppercase letters at the start or end of the pattern string.

    Parameters
    ----------
    pattern_string : str
        The string to be matched against.
    target_string : str
        The string to be matched.

    Returns
    -------
    bool
        True if the target string matches the pattern string, False otherwise.
    """
    start_pattern = r'^([A-Z]+)([a-z_]+)$'
    end_pattern = r'^([a-z_]+)([A-Z]+)$'
    
    start_match = re.match(start_pattern, pattern_string)
    end_match = re.match(end_pattern, pattern_string)
    
    if start_match:
        lowercase_part = start_match.group(2)
        target_pattern = f'^[a-z_]+{re.escape(lowercase_part)}$'
        if re.match(target_pattern, target_string):
            return True
    elif end_match:
        lowercase_part = end_match.group(1)
        target_pattern = f'^{re.escape(lowercase_part)}[a-z_]+$'
        if re.match(target_pattern, target_string):
            return True
    
    return False


def check_nametype(item_value):
    """
    Return the value of the 'nameType' attribute for a given item.

    Parameters
    ----------
    item_value : dict
        The dictionary representation of the item.

    Returns
    -------
    str
        The value of the 'nameType' attribute.
    """
    if '@nameType' in item_value:
        return item_value['@nameType']
    else:
        return 'specified'


def check_dimension_sizes(dimensions):
    """
    Check if a list of values are all within one of each other.
    
    This handles the case where axis bin boundaries are stored.

    Parameters
    ----------
    dimensions : list
        The list of dimensions to be checked.

    Returns
    -------
    bool
        True if dimensions are the same to within ± 1, False otherwise.
    """
    if not dimensions:
        return False
    min_dimension = min(dimensions)
    max_dimension = max(dimensions)
    return max_dimension - min_dimension <= 1


class StreamHandler(logging.StreamHandler):

    def __init__(self, stream=None, max_width=None):
        super().__init__(stream)
        if max_width is None:
            self.max_width = os.get_terminal_size().columns - 3
        else:
            self.max_width = max_width
        self.terminator = '\n'

    def emit(self, record):
        try:
            msg = self.format(record)
            truncated_msg = msg[:self.max_width]
            stream = self.stream
            stream.write(truncated_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class ColorFormatter(logging.Formatter):
    orange = "\x1b[1m\x1b[38;2;255;128;0m"
    red = "\x1b[1;31m\x1b[4:0m"
    reset = "\x1b[0m"

    format_string = "%(message)s"
    clear = "\x1b[0m"

    FORMATS = {
        logging.INFO: format_string,
        logging.WARNING: orange + format_string + reset,
        logging.ERROR: red + format_string + reset,
        logging.CRITICAL: format_string
    }
    def format(self, record):
        level = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(level)
        return formatter.format(record)
