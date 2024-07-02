
# Try to open a NeXus definition file

import xml
import h5py 
import xml.etree.ElementTree as ET

def get_valid_entries(file_path, tag):
    tree = ET.parse(file_path)
    root = tree.getroot()
    valid_list = []
    
    if tag == 'Field' or tag == 'field':
        valid_list = []
        for field in root.findall('.//{http://definition.nexusformat.org/nxdl/3.1}field'):
            name = field.get('name')
            if name:
                valid_list.append(name)       
                     
    elif tag == 'Group' or tag == 'group':
        valid_list = []
        for group in root.findall('.//{http://definition.nexusformat.org/nxdl/3.1}group'):
            type = group.get('type')
            if type:
                valid_list.append(type)
    else:
        print('Invalid function argument: must be field or group')
    
    return valid_list 

fields = get_valid_entries('/Users/kaitlyn/Desktop/argonne/nxvalidate/definitions/base_classes/NXsample.nxdl.xml', 'field')
for name in fields:
    print(name)
    
groups = get_valid_entries('/Users/kaitlyn/Desktop/argonne/nxvalidate/definitions/base_classes/NXsample.nxdl.xml', 'group')
for type in groups:
    print(type)
    
attributes = get_valid_entries('/Users/kaitlyn/Desktop/argonne/nxvalidate/definitions/base_classes/NXsample.nxdl.xml', 'attribute')


