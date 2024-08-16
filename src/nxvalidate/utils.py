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
