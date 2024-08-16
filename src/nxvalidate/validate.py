import logging
import sys
import xml
import xml.etree.ElementTree as ET
from importlib.resources import files as package_files

import numpy as np
from nexusformat.nexus import *
from utils import is_valid_float, is_valid_int, is_valid_iso8601

# Global dictionary of validators 
validators = {}
logger = None 


# def setup_logger(logger):
#     """ Set up the logger for development use """
#     logger.setLevel(logging.DEBUG)
#     h = logging.StreamHandler(stream=sys.stdout)
#     fmtr = logging.Formatter(
#             "%(asctime)s %(name)s %(levelname)-5s %(message)s",
#             datefmt="%Y-%m-%d %H:%M:%S")
#     h.setFormatter(fmtr)
#     logger.addHandler(h)
#     return logger


def get_logger(): 
    global logger
    if logger is None:
        logger = logging.getLogger("validate")
        logger.info("NXVALIDATE")
        logger.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        logger.addHandler(stream_handler)
    return logger 

def get_validator(nxclass):
    if nxclass not in validators: 
        validators[nxclass] = GroupValidator(nxclass)
    return validators[nxclass]

class Validator():
    
    # move the logger 
    def __init__(self):
        self.logger = logger 
        
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
                    valid_list[name] = field.attrib
                    
                        
        elif tag.lower() ==  'group':
            valid_list = {}
            for group in root.findall('.//{%s}group' % namespace):
                type = group.get('type')
                if type:
                    valid_list[type] = {}
                    
                    min_occurs = group.get('minOccurs')
                    
                    if min_occurs:
                        valid_list[type]['minOccurs'] = int(min_occurs)
 
                        # valid_list[type].append({'minOccurs': int(min_occurs)})
                    

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
    
    def check_type(self, entry, item):
        if 'type' in self.valid_fields[entry]:
            dtype = self.valid_fields[entry]['type'] 
        else:
            return 
        
        if dtype == 'NX_DATE_TIME': 
            if is_valid_iso8601(item.nxvalue):
                logger.info(f'"{item.nxname}" is a valid date')
            else:
                logger.warning(f'"{item.nxname}" is not a valid date')
        elif dtype == 'NX_INT':
            if is_valid_int(item.dtype):
                logger.info(f'"{item.nxname}" is a valid integer')
            else:
                logger.warning(f'"{item.nxname}" is not a valid integer')
        elif dtype == 'NX_FLOAT':
            if is_valid_float(item.dtype):
                logger.info(f'"{item.nxname}" is a valid float')
            else:
                logger.warning(f'"{item.nxname}" is not a valid float')

    def check_units(self, entry, item):
        if 'units' in self.valid_fields[entry]:
            if 'units' in item.attrs:
                logger.info('units specified')
            else:
                logger.warning('units not specified')

    def validate(self, group): 
        
        get_logger()
        
        for attribute in group.attrs:
            if attribute in self.valid_attributes:
                logger.info(f'{attribute} is a valid attribute of {group.nxpath}')
            else:
                logger.warning(f'{attribute} not defined')
                
        # group is the item 
        for entry in group.entries: # entries is a dictionary of all the items 
            item = group.entries[entry]

            if entry in self.valid_fields:
                if self.valid_fields[entry] != []:  
                    logger.info(f'{entry}:{self.valid_fields[entry]} is a valid member of {group.nxpath}')
                else:
                    logger.info(f'{entry} is a valid member of {group.nxpath}') 
                
                self.check_type(entry, item)
                self.check_units(entry, item)
                
            elif item.nxclass in self.valid_groups:
                logger.info(f'{entry}:{item.nxclass} is a valid member of {group.nxpath}')
            else:
                logger.warning(f'{entry} not defined in {group.nxname}')
                
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
                logger.info(f'{attribute} is a valid attribute of {field.nxpath}')
            else:
                logger.warning(f'{attribute} not defined in {field.nxname}')


def validate(filename, path=None):
    
    with nxopen(filename) as root:
        if path:
            root = root[path]
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