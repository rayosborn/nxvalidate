import logging
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np
from nexusformat.nexus import NXfield, NXgroup, nxopen

from .utils import (is_valid_float, is_valid_int, is_valid_iso8601,
                    package_files, strip_namespace)


name_pattern = re.compile('^[a-zA-Z0-9_]([a-zA-Z0-9_.]*[a-zA-Z0-9_])?$')

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
    
    def __init__(self):
        self.logged_messages = []
        
    def get_valid_entries(self, base_class, tag):
        valid_list = {}

        file_path = package_files('nxvalidate.definitions.base_classes'
                                  ).joinpath(f'{base_class}.nxdl.xml')
        if file_path.exists():
            tree = ET.parse(file_path)
        else:
            return valid_list
        root = tree.getroot()
        strip_namespace(root)
    
        if tag.lower() == 'field':
            valid_list = {}
            for field in root.findall('field'):
                name = field.get('name')
                if name:
                    valid_list[name] = {k: v for k, v in field.attrib.items()
                                        if k != 'name'}
                        
        elif tag.lower() ==  'group':
            valid_list = {}
            for group in root.findall('group'):
                group_type = group.get('type')
                if group_type:
                    valid_list[group_type] = {k: v 
                        for k, v in group.attrib.items() if k != 'type'}                    

        elif tag.lower() == 'attribute':
            valid_list = []
            for attribute in root.findall('attribute'):
                name = attribute.get('name')
                if name:
                    valid_list.append(name)
        
        return valid_list

    def is_valid_name(self, name):
        if re.match(name_pattern, name):
            return True
        else:
            return False

    def log(self, message, level='info', indent=0):
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
        if logger.level != logging.INFO and warning == 0 and error == 1:
            self.logged_messages = []
            return
        for message, level, indent in self.logged_messages:
            log(message, level=level, indent=indent)
        self.logged_messages = []


class GroupValidator(Validator):

    def __init__(self, nxclass):
        super().__init__() 
        self.nxclass = nxclass 
        self.valid_fields = self.get_valid_fields()
        self.valid_groups = self.get_valid_groups()
        self.valid_attributes = self.get_valid_attributes()

    def get_valid_fields(self):
        return self.get_valid_entries(self.nxclass, 'field')
    
    def get_valid_groups(self):
        return self.get_valid_entries(self.nxclass, 'group')
    
    def get_valid_attributes(self):
        return self.get_valid_entries(self.nxclass, 'attribute')
    
    def validate(self, group): 

        self.logged_messages = []
        self.log(f'Group: {group.nxpath}', level='error')        
        for attribute in group.attrs:
            if attribute in self.valid_attributes:
                self.log(f'"@{attribute}" is a valid attribute of the base class {group.nxclass}', indent=1)
            else:
                self.log(f'"@{attribute}" not defined as an attribute in the base class {group.nxclass}', level='info', indent=1)
                
        for entry in group.entries: # entries is a dictionary of all the items 
            item = group.entries[entry]
            if entry in self.valid_fields:
                field_validator.validate(self.valid_fields[entry], item)                
            elif item.nxclass in self.valid_groups:
                self.log(f'"{entry}":{item.nxclass} is a valid group in the base class {group.nxclass},', indent=1)
            elif self.is_valid_name(entry):
                if isinstance(item, NXgroup):
                    self.log(f'"{entry}":{item.nxclass} is not a valid base class in {group.nxclass}', level='warning', indent=1)
                elif isinstance(item, NXfield):
                    if group.nxclass == 'NXdata':
                        self.log(f'Field "{entry}" is an allowed field in the base class {group.nxclass}', level='info', indent=1)
                    else:
                        self.log(f'Field "{entry}" not defined in the base class {group.nxclass}', level='warning', indent=1)
            else:
                self.log(f'"{entry}" in {group.nxpath} is an invalid name', level='error', indent=1)
        self.output_log()
                

class FieldValidator(Validator):

    def __init__(self):
        super().__init__() 

    def check_type(self, tag, field):
        if 'type' in tag:
            dtype = tag['type'] 
        else:
            return 
        if dtype == 'NX_DATE_TIME': 
            if is_valid_iso8601(field.nxvalue):
                self.log(f'"{field.nxname}" is a valid date', indent=2)
            else:
                self.log(f'"{field.nxname}" is not a valid date', level='warning', indent=2)
        elif dtype == 'NX_INT':
            if is_valid_int(field.dtype):
                self.log(f'"{field.nxname}" is a valid integer', indent=2)
            else:
                self.log(f'"{field.nxname}" is not a valid integer', level='warning', indent=2)
        elif dtype == 'NX_FLOAT':
            if is_valid_float(field.dtype):
                self.log(f'"{field.nxname}" is a valid float', indent=2)
            else:
                self.log(f'"{field.nxname}" is not a valid float', level='warning', indent=2)

        # Add other datatypes

    def check_units(self, tag, field):
        if 'units' in tag:
            if 'units' in field.attrs:
                log(f'"{field.attrs["units"]}" are specified as the units of "{field.nxname}"', indent=2)
            else:
                pass
                self.log('Units not specified', level='warning', indent=2)

    def validate(self, tag, field):
        self.logged_messages = []
        self.log(f'Field: {field.nxpath}', level='error', indent=1)
        self.log(f'"{field.nxname}" is a valid field in {field.nxgroup.nxpath}', indent=2)     
        self.check_type(tag, field)
        self.check_units(tag, field)
        self.output_log()


field_validator = FieldValidator()


def validate_file(filename, path=None):
 
    with nxopen(filename) as root:
        if path:
            root = root[path]
        for item in root.walk():
            if isinstance(item, NXgroup):
                validator = get_validator(item.nxclass)
                validator.validate(item)

def validate_application(application, filename, path='/'):
    with nxopen(filename) as root:
        nxpath = path
    if 'definition' in root:
        application = root['definition']
    app_path = package_files('nxvalidate.definitions.applications'
                             ).joinpath(f'{application}.nxdl.xml')
    if app_path.exists():
        tree = ET.parse(app_path)
    else:
        return
    xml_root = tree.getroot()
    strip_namespace(xml_root)
    
    def walk(element, level=0):
        yield element, level
        for child in element:
            yield from walk(child, level + 1)

    for elem, level in walk(xml_root):
        indent = "  " * level
        print(f"{indent}{elem.tag}: {elem.text.strip() if elem.text else ''}")
        for name, value in elem.attrib.items():
            nxpath = nxpath + '/' + elem.attrib['name']
            group = root[nxpath]
            print(f"{indent}  @{name} = {value}")

def report(base_class):
    validator = get_validator(base_class)
    log(f"Base Class: {base_class}")
    log('Defined Attributes', indent=1)
    for attribute in validator.valid_attributes:
        log(f"@{attribute}", indent=2)
    log('    Defined Groups')
    for group in validator.valid_groups:
        log(f"{group}", indent=2)
    log('    Defined Fields')              
    for field in validator.valid_fields:
        log(f"{field}: {validator.valid_fields[field]}", indent=2)


def log(message, level='info', indent=0):
    if level == 'info':
        logger.info(f'{4*indent*" "}{message}')
    elif level == 'debug':
        logger.log(logging.DEBUG, f'{4*indent*" "}{message}')
    elif level == 'warning':
        logger.warning(f'{4*indent*" "}{message}')
    elif level == 'error':
        logger.error(f'{4*indent*" "}{message}')
    

if __name__ == "__main__":
    chopper = '/Users/kaitlyn/Desktop/argonne/nxvalidate/demos/chopper.nxs'
    validate_file(chopper)