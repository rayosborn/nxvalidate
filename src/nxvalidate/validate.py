import logging
import sys
import xml.etree.ElementTree as ET

import numpy as np
from nexusformat.nexus import *

from .utils import (is_valid_float, is_valid_int, is_valid_iso8601,
                    package_files, strip_namespace)

# Global dictionary of validators 
validators = {}

def get_logger(): 
    logger = logging.getLogger("validate")
    logger.info("NXVALIDATE")
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
        pass
        
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
        
        for attribute in group.attrs:
            if attribute in self.valid_attributes:
                logger.info(f'{attribute} is a valid attribute of {group.nxpath}')
            else:
                logger.warning(f'{attribute} not defined')
                
        for entry in group.entries: # entries is a dictionary of all the items 
            item = group.entries[entry]
            if entry in self.valid_fields:
                logger.info(f'{entry} is a valid member of {group.nxpath}')
                field_validator.validate(self.valid_fields[entry], item)                
            elif item.nxclass in self.valid_groups:
                logger.info(f'{entry}:{item.nxclass} is a valid member of {group.nxpath}')
            else:
                logger.warning(f'{entry} not defined in {group.nxname}')
                

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
                logger.info(f'"{field.nxname}" is a valid date')
            else:
                logger.warning(f'"{field.nxname}" is not a valid date')
        elif dtype == 'NX_INT':
            if is_valid_int(field.dtype):
                logger.info(f'"{field.nxname}" is a valid integer')
            else:
                logger.warning(f'"{field.nxname}" is not a valid integer')
        elif dtype == 'NX_FLOAT':
            if is_valid_float(field.dtype):
                logger.info(f'"{field.nxname}" is a valid float')
            else:
                logger.warning(f'"{field.nxname}" is not a valid float')

        # Add other datatypes

    def check_units(self, tag, field):
        if 'units' in tag:
            if 'units' in field.attrs:
                logger.info('units specified')
            else:
                logger.warning('units not specified')

    def validate(self, tag, field):
        self.check_type(tag, field)
        self.check_units(tag, field)


field_validator = FieldValidator()


def validate(filename, path=None):
    
    with nxopen(filename) as root:
        if path:
            root = root[path]
        for item in root.walk():
            if isinstance(item, NXgroup):
                validator = get_validator(item.nxclass)
                validator.validate(item)


def report(base_class):
    validator = get_validator(base_class)
    logger.info(f"Base Class: {base_class}")
    logger.info('    Defined Attributes')
    for attribute in validator.valid_attributes:
        logger.info(f"        @{attribute}")
    logger.info('    Defined Groups')
    for group in validator.valid_groups:
        logger.info(f"        {group}")
    logger.info('    Defined Fields')              
    for field in validator.valid_fields:
        logger.info(f"        {field}")


if __name__ == "__main__":
    chopper = '/Users/kaitlyn/Desktop/argonne/nxvalidate/demos/chopper.nxs'
    validate(chopper)