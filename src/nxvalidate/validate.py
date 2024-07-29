import xml
import logging
import xml.etree.ElementTree as ET
from importlib.resources import files as package_files

import numpy as np
from nexusformat.nexus import *

filename = package_files('nxvalidate.examples').joinpath('chopper.nxs')
valid_groups = {}


# Validator superclass 
class Validator():

    def __init__(self):
        # Added logger to Validator superclass
        self.logger = logging.getLogger('nxvalidate')
        self.logger.setLevel(logging.DEBUG)
        self.stream_handler = logging.StreamHandler(stream=sys.stdout)
        self.formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        self.stream_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.stream_handler)
        
    def get_valid_entries(base_class, tag):
        valid_list = []

        file_path = package_files('nxvalidate.definitions.base_classes').joinpath(
                f'{base_class}.nxdl.xml')
        if file_path.exists():
            tree = ET.parse(file_path)
        else:
            return valid_list        
        root = tree.getroot()
        
        namespace = root.tag.split('}')[0][1:]
        # Changed string handling 
    
        if tag.lower() == 'field':
            valid_list = []
            for field in root.findall('.//{%s}field' % namespace):
                name = field.get('name')
                if name:
                    valid_list.append(name)       
                        
        elif tag.lower() ==  'group':
            valid_list = []
            for group in root.findall('.//{%s}group' % namespace):
                type = group.get('type')
                if type:
                    valid_list.append(type)

        # Added attributes method 
        elif tag.lower() == 'attribute':
            valid_list = []
            for attribute in root.findall('.//{%s}attribute' % namespace):
                name = attribute.get('name')
                if name:
                    valid_list.append(name)
        
        return valid_list 

class GroupValidator(Validator):

    def __init__(self, group):
        super().__init__() # Inherits from Validator superlcass 
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
            valid_groups[self.nxclass] = self.get_valid_entries(self.nxclass, 'group')
            return valid_groups[self.nxclass]
        except Exception as error:
            return []

    def get_valid_fields(self):
        return self.get_valid_entries(self.nxclass, 'field')

    def validate(self):
        if self.validator is not None:
            if self.nxclass in self.validator.valid_groups:
                self.logger.info(f'{self.group.nxname}:{self.group.nxclass}')
            else:
                self.logger.info(f'{self.group.nxname} unspecified')


class FieldValidator(Validator):

    def __init__(self, field):
        super().__init__() # Inherits from Validator superlcass
        self.field = field
        self.validator = GroupValidator(self.field.nxgroup)

    def validate(self):
        if self.field.nxname in self.validator.valid_fields:
            self.logger.info(f'{self.field.nxname}: value={self.field.nxvalue}')
        else:
            self.logger.info(f'{self.field.nxname} unspecified')


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