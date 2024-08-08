import xml
import sys 
import logging
import xml.etree.ElementTree as ET
from importlib.resources import files as package_files

import numpy as np
from nexusformat.nexus import *

# Global dictionary of validators 
validators = {}

def get_validator(nxclass):
    if nxclass not in validators: 
        validators[nxclass] = GroupValidator(nxclass)
    return validators[nxclass]

class Validator():

    def __init__(self):
        self.logger = logging.getLogger('nxvalidate')
        self.logger.setLevel(logging.DEBUG)
        self.stream_handler = logging.StreamHandler(stream=sys.stdout)
        self.logger.addHandler(self.stream_handler)
        
    def get_valid_entries(self, base_class, tag):
        valid_list = {}

        file_path = package_files('nxvalidate.definitions.base_classes').joinpath(
                f'{base_class}.nxdl.xml')
        if file_path.exists():
            tree = ET.parse(file_path)
        else:
            return valid_list        
        root = tree.getroot()
        
        namespace = root.tag.split('}')[0][1:]
    
        if tag.lower() == 'field':
            valid_list = {}
            for field in root.findall('.//{%s}field' % namespace):
                name = field.get('name')
                if name:
                    valid_list[name] = [] 
                    
                    type = field.get('type')
                    min_occurs = field.get('minOccurs')
                    
                    if type: 
                        valid_list[name].append({'type': type})     
                    if min_occurs:
                        valid_list[name].append({'minOccurs': int(min_occurs)})
     
                        
        elif tag.lower() ==  'group':
            valid_list = {}
            for group in root.findall('.//{%s}group' % namespace):
                type = group.get('type')
                if type:
                    valid_list[type] = []
                    
                    min_occurs = group.get('minOccurs')
                    
                    if min_occurs:
                        valid_list[type].append({'minOccurs': int(min_occurs)})
                    

        elif tag.lower() == 'attribute':
            valid_list = [] # List instead of dictionary
            for attribute in root.findall('.//{%s}attribute' % namespace):
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

        # if self.group.nxgroup:
        #     self.validator = GroupValidator(self.group.nxgroup) 
        # else:
        #     self.validator = None

    def get_valid_fields(self):
        return self.get_valid_entries(self.nxclass, 'field')
    
    def get_valid_groups(self):
        return self.get_valid_entries(self.nxclass, 'group')
    
    def get_valid_attributes(self):
        return self.get_valid_entries(self.nxclass, 'attribute')

    def validate(self, group): 
        for attribute in group.attrs:
            
            if attribute in self.valid_attributes:
                self.logger.info(f'{attribute} is a valid attribute of {group.nxpath}')
            else:
                self.logger.info(f'{attribute} not defined')
                
        # group is the item 
        for entry in group.entries: # entries is a dictionary of all the items 
            item = group.entries[entry]
            if entry in self.valid_fields:
                if self.valid_fields[entry] != []:  
                    self.logger.info(f'{entry}:{self.valid_fields[entry]} is a valid member of {group.nxpath}')
                else:
                    self.logger.info(f'{entry} is a valid member of {group.nxpath}')
                # self.check_type()
            elif item.nxclass in self.valid_groups:
                self.logger.info(f'{entry}:{item.nxclass} is a valid member of {group.nxpath}')
            else:
                self.logger.info(f'{entry} not defined')
                
            # do another check for if the type that's defined in the group is the right type 
            # for NXfield 
            # valid fields ought to be a dictionary where the key is the field name and the entry is the field type 
            # print('f{entry}:{valid_fields[entry]} is a valid field)

class FieldValidator(Validator):

    def __init__(self):
        super().__init__() 
        self.validator = GroupValidator(self.field.nxgroup)
        self.valid_attributes = self.get_valid_attributes()

    def validate(self, field):
        for attribute in field.attrs:
            if attribute in self.valid_attributes:
                self.logger.info(f'{attribute} is a valid attribute of {field.nxpath}')
            else:
                self.logger.info(f'{attribute} not defined')


def validate(filename):

    with nxopen(filename) as root:
        for item in root.walk(): # go through every item in group
            if isinstance(item, NXgroup): # if the item is an NXgroup
                validator = get_validator(item.nxclass) # get the validator for that particular class of that group this returns the NXsample version of that validator
                validator.validate(item) # let's validate the item itself which is the group
                # when you call the validate function you are validating the item knowing the information the validator stores about the class 
           
            # elif isinstance(item, NXfield):
            #     validator = FieldValidator(item)
                

if __name__ == "__main__":
    chopper = '/Users/kaitlyn/Desktop/argonne/nxvalidate/demos/chopper.nxs'
    validate(chopper)