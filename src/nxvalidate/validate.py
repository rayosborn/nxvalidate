import xml
import xml.etree.ElementTree as ET
from importlib.resources import files

import numpy as np
from nexusformat.nexus import *

filename = files('nxvalidate.examples').joinpath('chopper.nxs')
valid_groups = {}

def get_valid_entries(base_class, tag):
    valid_list = []

    file_path = files('nxvalidate.definitions.base_classes').joinpath(
        f'{base_class}.nxdl.xml')
    if file_path.exists():
        tree = ET.parse(file_path)
    else:
        return valid_list        
    root = tree.getroot()
    
    if tag.lower() == 'field':
        valid_list = []
        for field in root.findall('.//{http://definition.nexusformat.org/nxdl/3.1}field'):
            name = field.get('name')
            if name:
                valid_list.append(name)       
                     
    elif tag.lower() == 'group':
        valid_list = []
        for group in root.findall('.//{http://definition.nexusformat.org/nxdl/3.1}group'):
            type = group.get('type')
            if type:
                valid_list.append(type)
    else:
        print('Invalid function argument: must be field or group')
    
    return valid_list 

class GroupValidator():

    def __init__(self, group):
        self.group = group
        self.nxclass = self.group.nxclass
        self.valid_fields = self.get_valid_fields()
        self.valid_groups = self.get_valid_groups()
        if self.group.nxgroup:
            self.validator = GroupValidator(self.group.nxgroup)
        else:
            self.validator = None

    def get_valid_groups(self):
        if self.nxclass in valid_groups:
            return valid_groups[self.nxclass]
        try:
            valid_groups[self.nxclass] = get_valid_entries(self.nxclass, 'group')
            return valid_groups[self.nxclass]
        except Exception as error:
            return []

    def get_valid_fields(self):
        return get_valid_entries(self.nxclass, 'field')

    def validate(self):
        if self.validator is not None:
            if self.nxclass in self.validator.valid_groups:
                print(f'{self.group.nxname}:{self.group.nxclass}')
            else:
                print(f'{self.group.nxname} unspecified')


class FieldValidator():

    def __init__(self, field):
        self.field = field
        self.validator = GroupValidator(self.field.nxgroup)

    def validate(self):
        if self.field.nxname in self.validator.valid_fields:
            print(f'{self.field.nxname}: value={self.field.nxvalue}')
        else:
            print(f'{self.field.nxname} unspecified')


def validate():

    with nxopen(filename) as root:
        for item in root.walk():
            if isinstance(item, NXgroup):
                validator = GroupValidator(item)
            elif isinstance(item, NXfield):
                validator = FieldValidator(item)
            if validator is not None:
                validator.validate()


if __name__ == "__main__":
    validate()
