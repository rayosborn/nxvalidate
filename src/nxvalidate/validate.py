import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import PosixPath as Path

import numpy as np
from nexusformat.nexus import NeXusError, NXentry, NXgroup, NXsubentry, nxopen

from .utils import (is_valid_bool, is_valid_char, is_valid_char_or_number,
                    is_valid_complex, is_valid_float, is_valid_int,
                    is_valid_iso8601, is_valid_name, is_valid_number,
                    is_valid_posint, is_valid_uint, package_files,
                    strip_namespace)

# Global dictionary of validators 
validators = {}

def get_logger(): 
    logger = logging.getLogger("NXValidate")
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(stream_handler)
    return logger 


logger = get_logger()


def get_validator(nxclass):
    if nxclass not in validators:
        validators[nxclass] = GroupValidator(nxclass)
    return validators[nxclass]


class Validator():
    
    def __init__(self, nxclass=None):
        self.nxclass = nxclass
        self.logged_messages = []
        self.valid_class = True
        if self.nxclass != 'NXfield':
            self.root = self.get_root()
        else:
            self.root = None
        self.parent = None

    def get_root(self):
        if self.nxclass:
            file_path = package_files('nxvalidate.definitions.base_classes'
                                      ).joinpath(f'{self.nxclass}.nxdl.xml')
            if file_path.exists():
                tree = ET.parse(file_path)
                root = tree.getroot()
                strip_namespace(root)
            else:
                root = None
                self.valid_class = False
        else:
            root = None
        return root

    def get_attributes(self, item):
        try:
            return {k: v for k, v in item.attrib.items()}
        except Exception:
            return {}

    def log(self, message, level='info', indent=None):
        if indent is None:
            indent = self.indent
        self.logged_messages.append((message, level, indent))

    def output_log(self):
        info = 0
        warning = 0
        error = 0
        debug = 0
        for item in self.logged_messages:
            if item[1] == 'info':
                info += 1
            elif item[1] == 'warning':
                warning += 1
            elif item[1] == 'error':
                error += 1
            elif item[1] == 'debug':
                debug += 1
        if ((logger.level == logging.WARNING and warning == 0 and error == 0)
                or (logger.level == logging.ERROR and error == 0)):
            self.logged_messages = []
            return
        for message, level, indent in self.logged_messages:
            if level == 'all':
                level = 'error'
            log(message, level=level, indent=indent)
        self.logged_messages = []


class GroupValidator(Validator):

    def __init__(self, nxclass):
        super().__init__(nxclass)
        if self.valid_class:
            self.valid_fields = self.get_valid_fields()
            self.valid_groups = self.get_valid_groups()
            self.valid_attributes = self.get_valid_attributes()

    def get_valid_fields(self):
        valid_fields = {}
        if self.root is not None:
            for field in self.root.findall('field'):
                name = field.get('name')
                if name:
                    valid_fields[name] = self.get_attributes(field)
        return valid_fields
    
    def get_valid_groups(self):
        valid_groups = {}
        if self.root is not None:
            for group in self.root.findall('group'):
                group_type = group.get('type')
                if group_type:
                    valid_groups[group_type] = self.get_attributes(group)
        return valid_groups
    
    def get_valid_attributes(self):
        valid_attrs = {}
        if self.root is not None:
            for attr in self.root.findall('attribute'):
                name = attr.get('name')
                if name:
                    valid_attrs[name] = self.get_attributes(attr)
        return valid_attrs
    
    def validate(self, group, indent=0): 
        self.indent = indent
        self.log(f'{group.nxclass}: {group.nxpath}', level='all')
        self.indent += 1
        if not is_valid_name(group.nxname):
            self.log(f'"{group.nxname}" is an invalid name', level='error')
        if not self.valid_class:
            self.log(f'{group.nxclass} is not a valid base class', level='error')
            self.output_log()
            return
        parent = group.nxgroup
        if parent:
            parent_validator = get_validator(parent.nxclass)
            if group.nxclass not in parent_validator.valid_groups:
                self.log(f'{group.nxclass} is an invalid class in {parent.nxclass}', 
                         level='error')            

        for attribute in group.attrs:
            if attribute in self.valid_attributes:
                self.log(
                    f'"@{attribute}" is a valid attribute of the base class {group.nxclass}')
            else:
                self.log(f'"@{attribute}" not defined as an attribute in the base class {group.nxclass}', 
                         level='info')
        if group.nxclass == 'NXdata':
            if 'signal' in group.attrs:
                signal = group.attrs['signal']
                if signal not in group.entries:
                    self.log(f'@signal={signal}" not present in group "{group.nxpath}"',
                             level='error')
            else:
                self.log(f'"@signal" not defined in NXdata group "{group.nxpath}"',
                         level='error')

        for entry in group.entries: 
            item = group.entries[entry]
            if item.nxclass == 'NXfield':
                if entry in self.valid_fields:
                    tag = self.valid_fields[entry]
                else:
                    tag = {}
                field_validator.validate(tag, item, parent=self, indent=indent)
        self.output_log()
                

class FieldValidator(Validator):

    def __init__(self):
        super().__init__(nxclass='NXfield')

    def check_type(self, tag, field):
        if 'type' in tag:
            dtype = tag['type'] 
        else:
            return 
        if dtype == 'NX_DATE_TIME': 
            if is_valid_iso8601(field.nxvalue):
                self.log(f'"{field.nxname}" is a valid NX_DATE_TIME')
            else:
                self.log(f'"{field.nxname}" is not a valid NX_DATE_TIME', level='warning')
        elif dtype == 'NX_INT':
            if is_valid_int(field.dtype):
                self.log(f'"{field.nxname}" is a valid NX_INT')
            else:
                self.log(f'"{field.nxname}" is not a valid NX_INT', level='warning')
        elif dtype == 'NX_FLOAT':
            if is_valid_float(field.dtype):
                self.log(f'"{field.nxname}" is a valid NX_FLOAT')
            else:
                self.log(f'"{field.nxname}" is not a valid fNX_FLOAT', level='warning')
        elif dtype == 'NX_BOOLEAN':
            if is_valid_bool(field.dtype):
                self.log(f'"{field.nxname}" is a valid NX_BOOLEAN')
            else:
                self.log(f'"{field.nxname}" is not a valid NX_BOOLEAN', level='warning')         
        elif dtype == 'NX_CHAR':
            if is_valid_char(field.dtype):
                self.log(f'"{field.nxname}" is a valid NX_CHAR')
            else:
                self.log(f'"{field.nxname}" is not a valid NX_CHAR',
                         level='warning')                  
        elif dtype == 'NX_CHAR_OR_NUMBER':
            if is_valid_char_or_number(field.dtype):
                self.log(f'"{field.nxname}" is a valid NX_CHAR_OR_NUMBER')
            else:
                self.log(f'"{field.nxname}" is not a valid NX_CHAR_OR_NUMBER', level='warning')                
        elif dtype == 'NX_COMPLEX':
            if is_valid_complex(field.dtype):
                self.log(f'"{field.nxname}" is a valid NX_COMPLEX value')
            else:
                self.log(f'"{field.nxname}" is not a valid NX_COMPLEX value', level='warning') 
        elif dtype == 'NX_NUMBER':
            if is_valid_number(field.dtype):
                self.log(f'"{field.nxname}" is a valid NX_NUMBER')
            else:
                self.log(f'"{field.nxname}" is not a valid NX_NUMBER', level='warning')       
        elif dtype == 'NX_POSINT':
            if is_valid_posint(field.dtype):
                self.log(f'"{field.nxname}" is a valid NX_POSINT')
            else:
                self.log(f'"{field.nxname}" is not a valid NX_POSINT', level='warning')    
        elif dtype == 'NX_UINT':
            if is_valid_uint(field.dtype):
                self.log(f'"{field.nxname}" is a valid NX_UINT')
            else:
                self.log(f'"{field.nxname}" is not a valid NX_UINT', level='warning')        

    def check_attributes(self, tag, field):
        if 'signal' in field.attrs:
            self.log(f'Using "signal" as a field attribute is no longer valid. Use the group attribute "signal"', 
                     level='error')
        elif 'axis' in field.attrs:
            self.log(f'Using "axis" as a field attribute is no longer valid. Use the group attribute "axes"', 
                     level='error')
        if 'units' in field.attrs:
            if 'units' in tag:
                self.log(f'"{field.attrs["units"]}" are specified as units of {tag["units"]}')
            else:
                self.log(f'"{field.attrs["units"]}" are specified as units')
        elif 'units' in tag:
            self.log(f'Units of {tag["units"]} not specified', level='warning')
        for attr in [a for a in field.attrs if a not in ['axis', 'signal', 'units']]:
            self.log(f'"{attr}" is defined as an attribute')

    def output_log(self):
        info = 0
        warning = 0
        error = 0
        debug = 0
        for item in self.logged_messages:
            if item[1] == 'info':
                info += 1
            elif item[1] == 'warning':
                warning += 1
            elif item[1] == 'error':
                error += 1
            elif item[1] == 'debug':
                debug += 1
        if logger.level != logging.INFO and warning == 0 and error == 0:
            self.logged_messages = []
            return
        for message, level, indent in self.logged_messages:
            self.parent.logged_messages.append((message, level, indent))
        self.logged_messages = []

    def validate(self, tag, field, parent=None, indent=1):
        if parent:
            self.parent = parent
        else:
            self.parent = self
        group = field.nxgroup
        self.indent = indent + 1
        self.log(f'Field: {field.nxpath}', level='all')
        self.indent += 1
        if not is_valid_name(field.nxname):
            self.log(f'"{field.nxname}" is an invalid name', level='error')
        if tag:
            self.log(f'"{field.nxname}" is a valid field in the base class {group.nxclass}')
        else:    
            if group.nxclass in ['NXcollection', 'NXdata', 'NXprocess']:
                self.log(f'Field "{field.nxname}" is an allowed field in the base class {group.nxclass}')
            else:
                self.log(f'Field "{field.nxname}" not defined in the base class {group.nxclass}', 
                         level='warning')
        self.check_type(tag, field)
        self.check_attributes(tag, field)
        self.output_log()


field_validator = FieldValidator()


class FileValidator(Validator):

    def __init__(self, filename):
        self.filename = filename

    def walk(self, node, indent=0):
        if node.nxclass == 'NXfield':
            yield node, indent
        else:
            yield node, indent
            for child_node in node.entries.values():
                yield from self.walk(child_node, indent+1)

    def validate(self, path=None):
        with nxopen(self.filename) as root:
            if path:
                parent = root[path]
            else:
                parent = root
            for item, indent in self.walk(parent):
                if isinstance(item, NXgroup):
                    validator = get_validator(item.nxclass)
                    validator.validate(item, indent=indent)


        for child in element:

def validate_file(filename, path=None):

    validator = FileValidator(filename)
    validator.validate(path)



def output_base_class(base_class):
    validator = get_validator(base_class)
    log(f"Base Class: {base_class}")
    if validator.valid_attributes:
        for attribute in validator.valid_attributes:
            log(f"@{attribute}", indent=1)
    if validator.valid_groups:
        log('Allowed Groups', indent=1)
        for group in validator.valid_groups:
            log(f"{group}", indent=2)
    if validator.valid_fields:
        log('Defined Fields', indent=1)              
        for field in validator.valid_fields:
            log(f"{field}: {validator.valid_fields[field]}", indent=2)


def log(message, level='info', indent=0):
    if level == 'info':
        logger.info(f'{2*indent*" "}{message}')
    elif level == 'debug':
        logger.log(logging.DEBUG, f'{2*indent*" "}{message}')
    elif level == 'warning':
        logger.warning(f'{2*indent*" "}{message}')
    elif level == 'error':
        logger.error(f'{2*indent*" "}{message}')
