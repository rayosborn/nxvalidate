
# Try to open a NeXus definition file

import xml
import h5py 
import xml.etree.ElementTree as ET
from importlib.resources import files as package_files
import nxvalidate

filename = package_files('nxvalidate.examples').joinpath('chopper.nxs')
valid_groups = {}

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
    
    if tag == 'Field' or tag == 'field':
        valid_list = []
        for field in root.findall('.//{%s}field' % namespace):
            name = field.get('name')
            if name:
                valid_list.append(name)       
                     
    elif tag == 'Group' or tag == 'group':
        valid_list = []
        for group in root.findall('.//{%s}group' % namespace):
            type = group.get('type')
            if type:
                valid_list.append(type)

    elif tag.lower() == 'attribute':
        valid_list = []
        for attribute in root.findall('.//{%s}attribute' % namespace):
            name = attribute.get('name')
            if name:
                valid_list.append(name)
                            
    return valid_list 

fields = get_valid_entries('NXsample', 'field')
for name in fields:
    print(name)
    
groups = get_valid_entries('NXsample', 'group')
for type in groups:
    print(type)
    
attributes = get_valid_entries('NXsample', 'attribute')
for type in attributes:
    print(type)
