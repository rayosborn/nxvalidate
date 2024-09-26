# -----------------------------------------------------------------------------
# Copyright (c) 2024, Kaitlyn Marlor, Ray Osborn, Justin Wozniak.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------
import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from nexusformat.nexus import NeXusError, NXentry, NXgroup, NXsubentry, nxopen

from .utils import (is_valid_bool, is_valid_char, is_valid_char_or_number,
                    is_valid_complex, is_valid_float, is_valid_int,
                    is_valid_iso8601, is_valid_name, is_valid_number,
                    is_valid_posint, is_valid_uint, merge_dicts, package_files,
                    readaxes, strip_namespace, xml_to_dict)


def get_logger():
    """
    Returns a logger instance and sets the log level to DEBUG.

    The logger has a stream handler that writes to sys.stdout.

    Returns
    -------
    logger : logging.Logger
        A logger instance.
    """
    logger = logging.getLogger("NXValidate")
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(stream_handler)
    return logger 


logger = get_logger()


# Global dictionary of validators 
validators = {}


def get_validator(nxclass, definitions=None):
    """
    Retrieves a validator instance for a given NeXus class.

    Validators are stored in a global dictionary. If a validator has not
    already been created yet, it is created.

    Parameters
    ----------
    nxclass : str
        The name of the NeXus class to retrieve a validator for.

    Returns
    -------
    Validator
        A validator instance for the specified NeXus class.
    """
    if nxclass not in validators:
        validators[nxclass] = GroupValidator(nxclass, definitions=definitions)
    return validators[nxclass]


class Validator():
    
    def __init__(self, definitions=None):
        """
        Initializes a new Validator instance.
        """
        if definitions is not None:
            if isinstance(definitions, str):
                self.definitions = Path(definitions)
            else:
                self.definitions = definitions
        else:
            self.definitions = package_files('nxvalidate.definitions')
        self.baseclass_directory = self.definitions / 'base_classes'
        self.application_directory = self.definitions / 'applications'
        self.logged_messages = []
        self.indent = 0

    def get_attributes(self, element):
        """
        Retrieves the attributes of a given XML item as a dictionary.

        Parameters
        ----------
        element : XML.Element
            The item from which to retrieve attributes.

        Returns
        -------
        dict
            A dictionary containing the item's attributes.
        """
        try:
            result = {}
            result = {f"@{k}": v for k, v in element.attrib.items()}
            for child in element:
                if child.tag == 'enumeration':
                    result[child.tag] = [item.attrib['value']
                                         for item in child]
                elif child.tag != 'doc':
                    result[child.tag] = self.get_attributes(child)
            return result
        except Exception:
            return {}

    def log(self, message, level='info', indent=None):
        """
        Logs a message with a specified level and indentation.

        Parameters
        ----------
        message : str
            The message to be logged.
        level : str, optional
            The level of the message (default is 'info').
        indent : int, optional
            The indentation level of the message (default is None).
        """
        if indent is None:
            indent = self.indent
        self.logged_messages.append((message, level, indent))

    def output_log(self):
        """
        Outputs the logged messages and resets the log.

        This function iterates over the logged messages, counts the
        number of messages at each level, and logs each message using
        the log function. If the logger level is set to WARNING or ERROR
        and there are no messages at that level, the function resets the
        log and returns without logging any messages.
        """
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

    def __init__(self, nxclass, definitions=None):
        """
        Initialize a GroupValidator instance with the given NeXus class.

        Parameters
        ----------
        nxclass : str
            The NeXus class of the group to be validated.
        """
        super().__init__(definitions=definitions)
        self.nxclass = nxclass
        self.root = self.get_root()
        if self.valid_class:
            self.valid_fields = self.get_valid_fields()
            self.valid_groups = self.get_valid_groups()
            self.valid_attributes = self.get_valid_attributes()

    def get_root(self):
        """
        Retrieves the root element of the NeXus class XML file.

        If the NeXus class is specified and the corresponding XML file
        exists, this method parses the file and returns its root
        element. Otherwise, it returns None.

        Parameters
        ----------
        None

        Returns
        -------
        root : ElementTree.Element or None
            The root element of the NeXus class definition XML file, or
            None if the class is not specified or the file does not
            exist.
        """
        if self.nxclass:
            file_path = self.baseclass_directory / (f'{self.nxclass}.nxdl.xml')
            if file_path.exists():
                tree = ET.parse(file_path)
                root = tree.getroot()
                strip_namespace(root)
                self.valid_class = True
            else:
                root = None
                self.valid_class = False
        else:
            root = None
            self.valid_class = False
        return root

    def get_valid_fields(self):
        """
        Retrieves the valid fields from the XML root.

        Returns
        -------
        valid_fields : dict
            A dictionary containing the valid fields, where the keys are
            the field names and the values are the attributes of the
            field.
        """
        valid_fields = {}
        if self.root is not None:
            for field in self.root.findall('field'):
                name = field.get('name')
                if name:
                    valid_fields[name] = self.get_attributes(field)
        return valid_fields
    
    def get_valid_groups(self):
        """
        Retrieves the valid groups from the XML root.

        Returns
        -------
        valid_groups : dict
            A dictionary containing the valid groups, where the keys are
            the group types and the values are the attributes of the
            group.
        """
        valid_groups = {}
        if self.root is not None:
            for group in self.root.findall('group'):
                group_name = group.get('name')
                group_type = group.get('type')
                if group_name:
                    valid_groups[group_name] = self.get_attributes(group)
                elif group_type:
                    valid_groups[group_type] = self.get_attributes(group)
        return valid_groups
    
    def get_valid_attributes(self):
        """
        Retrieves the valid attributes from the XML root.

        Returns
        -------
        valid_attrs : dict
            A dictionary containing the valid attributes, where the keys
            are the attribute names and the values are the attribute
            values.
        """
        valid_attrs = {}
        if self.root is not None:
            for attr in self.root.findall('attribute'):
                name = attr.get('name')
                if name:
                    valid_attrs[name] = self.get_attributes(attr)
        return valid_attrs
    
    def validate(self, group, indent=0): 
        """
        Validates a given group against the NeXus standard.

        This function checks the validity of a group's name, class, and
        attributes. It also recursively validates the group's entries.

        Parameters
        ----------
        group : object
            The group to be validated.
        indent : int, optional
            The indentation level for logging (default is 0).
        """
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
                if 'ignoreExtraGroups' in parent_validator.root.attrib:
                    self.log(f'{group.nxclass} is not defined in '
                             f'{parent.nxclass}. '
                             'Additional classes are allowed.')
                else:
                    self.log(f'{group.nxclass} is an invalid class in '
                             f'{parent.nxclass}', level='error')

        for attribute in group.attrs:
            if attribute in self.valid_attributes:
                self.log(
                    f'"@{attribute}" is a valid attribute in {group.nxclass}')
            elif 'ignoreExtraAttributes' in self.root.attrib:
                self.log(
                    f'"@{attribute}" is not defined as an attribute in '
                    f'{group.nxclass}. Additional attributes are allowed.')
            else:
                self.log(
                    f'"@{attribute}" is not defined as an attribute'
                    f' in {group.nxclass}', level='warning')
        if group.nxclass == 'NXdata':
            if 'signal' in group.attrs:
                signal = group.attrs['signal']
                if signal not in group.entries:
                    self.log(
                        f'Signal "{signal}" not present in group'
                        f' "{group.nxpath}"', level='error')
            else:
                signal = None
                self.log(
                    f'"@signal" not defined in NXdata group "{group.nxpath}"',
                    level='error')
            if 'axes' in group.attrs:
                axes = readaxes(group.attrs['axes'])
                for axis in axes:
                    if axis != '.' and axis not in group.entries:
                        self.log(
                            f'Axis {axis}" not present in group '
                            f'"{group.nxpath}"', level='error')
                if signal in group:
                    if len(axes) != group[signal].ndim:
                        self.log(
                            '"@axes" length does not match the signal rank',
                            level='error')
                    else:
                        self.log('"@axes" has the correct length')
            else:
                self.log(
                    f'"@axes" not defined in NXdata group "{group.nxpath}"',
                    level='error')

        for entry in group.entries: 
            item = group.entries[entry]
            if item.nxclass == 'NXfield':
                if entry in self.valid_fields:
                    tag = self.valid_fields[entry]
                else:
                    tag = None
                field_validator.validate(tag, item, parent=self, indent=indent)
        self.output_log()
                

class FieldValidator(Validator):

    def __init__(self):
        """
        Initializes a FieldValidator instance.
        """
        super().__init__()

    def check_type(self, field, dtype):
        """
        Checks the data type of a given field.

        Parameters
        ----------
        field : object
            The field to be validated.
        dtype : str
            The NeXus data type to validate against.
        """
        if dtype == 'NX_DATE_TIME': 
            if is_valid_iso8601(field.nxvalue):
                self.log('This field is a valid NX_DATE_TIME')
            else:
                self.log('This field is not a valid NX_DATE_TIME',
                         level='warning')
        elif dtype == 'NX_INT':
            if is_valid_int(field.dtype):
                self.log('This field is a valid NX_INT')
            else:
                self.log('This field is not a valid NX_INT', level='warning')
        elif dtype == 'NX_FLOAT':
            if is_valid_float(field.dtype):
                self.log('This field is a valid NX_FLOAT')
            else:
                self.log('This field is not a valid fNX_FLOAT',
                         level='warning')
        elif dtype == 'NX_BOOLEAN':
            if is_valid_bool(field.dtype):
                self.log('This field is a valid NX_BOOLEAN')
            else:
                self.log('This field is not a valid NX_BOOLEAN',
                         level='warning')         
        elif dtype == 'NX_CHAR':
            if is_valid_char(field.dtype):
                self.log('This field is a valid NX_CHAR')
            else:
                self.log('This field is not a valid NX_CHAR',
                         level='warning')                  
        elif dtype == 'NX_CHAR_OR_NUMBER':
            if is_valid_char_or_number(field.dtype):
                self.log('This field is a valid NX_CHAR_OR_NUMBER')
            else:
                self.log('This field is not a valid NX_CHAR_OR_NUMBER',
                         level='warning')                
        elif dtype == 'NX_COMPLEX':
            if is_valid_complex(field.dtype):
                self.log('This field is a valid NX_COMPLEX value')
            else:
                self.log('This field is not a valid NX_COMPLEX value',
                         level='warning') 
        elif dtype == 'NX_NUMBER':
            if is_valid_number(field.dtype):
                self.log('This field is a valid NX_NUMBER')
            else:
                self.log('This field is not a valid NX_NUMBER',
                         level='warning')       
        elif dtype == 'NX_POSINT':
            if is_valid_posint(field.dtype):
                self.log('This field is a valid NX_POSINT')
            else:
                self.log(f'This field is not a valid NX_POSINT',
                         level='warning')    
        elif dtype == 'NX_UINT':
            if is_valid_uint(field.dtype):
                self.log(f'This field is a valid NX_UINT')
            else:
                self.log(f'This field is not a valid NX_UINT', level='warning')        

    def check_dimensions(self, field, dimensions):
        """
        Checks the dimensions of a field against the specified dimensions.
        
        Parameters
        ----------
        field : 
            The field to check dimensions for.
        dimensions : 
            The base class attribute containing the dimensions to check
            against.
        """

        if '@rank' in dimensions:
            try:
                rank = int(dimensions['@rank'])
            except ValueError:
                return
            if field.ndim == rank:
                self.log(f'The field has the correct rank of {rank}')
            else:
                self.log(f'The field has rank {field.ndim}, should be {rank}',
                         level='error')

    def check_enumeration(self, field, enumerations):
        """
        Checks if a field's value is a valid member of an enumerated list.

        Parameters
        ----------
        field : 
            The field to check the value for.
        enumerations : 
            The list of valid enumerated values.
        """
        if field.nxvalue in enumerations:
            self.log(
                f'The field value is a member of the enumerated list')
        else:
            self.log(
                f'The field value is not a member of the enumerated list',
                level='error') 

    def check_attributes(self, field, attributes=None, units=None):
        """
        Checks the attributes of a given field.

        Parameters
        ----------
        field : 
            The field to check attributes for.
        units : optional
            The units of the field. If provided, checks if the units are
            specified in the field attributes.
        """
        if 'signal' in field.attrs:
            self.log(
                f'Using "signal" as a field attribute is no longer valid. '
                'Use the group attribute "signal"', level='error')
        elif 'axis' in field.attrs:
            self.log(f'Using "axis" as a field attribute is no longer valid. '
                     'Use the group attribute "axes"', level='error')
        if 'units' in field.attrs:
            if units:
                self.log(
                    f'"{field.attrs["units"]}" are specified '
                    f'as units of {units}')
            else:
                self.log(f'"{field.attrs["units"]}" are specified as units')
        elif units:
            self.log(f'Units of {units} not specified', level='warning')
        checked_attributes = ['axis', 'signal', 'units']
        if attributes:
            for attr in attributes:
                if attr in field.attrs:
                    self.log(f'The suggested attribute "{attr}" is defined')
                else:
                    self.log(
                        f'The suggested attribute "{attr}" is not defined',
                        level='warning')
            checked_attributes += attributes
        for attr in [a for a in field.attrs if a not in checked_attributes]:
            self.log(f'"{attr}" is defined as an attribute')

    def output_log(self):
        """
        Outputs the logged messages and resets the log.

        This function iterates over the logged messages, counts the
        number of messages at each level, and logs each message using
        the log function. If the logger level is not set to INFO and
        there are no messages at the WARNING or ERROR level, the
        function resets the log and returns without logging any
        messages.
        """
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

    def validate(self, tag, field, parent=None, indent=1, minOccurs=None):
        """
        Validates a field in a NeXus group.

        Parameters
        ----------
        tag : dict
            A dictionary containing information about the field.
        field : object
            The field to be validated.
        parent : object, optional
            The parent object. Defaults to None.
        indent : int, optional
            The indentation level. Defaults to 1.
        """
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
        if minOccurs is not None:
            if minOccurs > 0:
                self.log(f'This is a required field in the NeXus file')
            else:
                self.log(f'This is an optional field in the NeXus file')
        elif tag is not None:
            self.log(f'This is a valid field in {group.nxclass}')
        if tag is None:
            if 'ignoreExtraFields' in self.parent.root.attrib:
                self.log(f'This field is not defined in {group.nxclass}. '
                         f'Additional fields are allowed.')
            else:
                self.log(f'This field is not defined in {group.nxclass}',
                         level='warning')
        else:    
            if '@deprecated' in tag:
                self.log(f'This field is now deprecated. {tag["@deprecated"]}',
                         level='warning')
            if '@type' in tag:  
                self.check_type(field, tag['@type'])
            if 'dimensions' in tag:
                self.check_dimensions(field, tag['dimensions'])
            if 'enumeration' in tag:
                self.check_enumeration(field, tag['enumeration'])
            if 'attribute' in tag:
                attributes = tag['attribute'].values()
            else:
                attributes = None
            if '@units' in tag:
                units = tag['@units']
            else:
                units = None
            self.check_attributes(field, attributes=attributes, units=units)
        self.output_log()


field_validator = FieldValidator()


class FileValidator(Validator):

    def __init__(self, filename, definitions=None):
        """
        Initializes a FileValidator instance with a filename.

        Parameters
        ----------
        filename : str
            The name of the file to be validated.
        """
        super().__init__(definitions=definitions)
        self.filename = filename

    def walk(self, node, indent=0):
        """
        Recursively walks through a node and its children.
        
        This function yeilds each node and its corresponding indentation
        level.

        Parameters
        ----------
        node : object
            The node to start walking from.
        indent : int, optional
            The current indentation level (default is 0).

        Yields
        ------
        tuple
            A tuple containing the current node and indentation level.
        """
        if node.nxclass == 'NXfield':
            yield node, indent
        else:
            yield node, indent
            for child_node in node.entries.values():
                yield from self.walk(child_node, indent+1)

    def validate(self, path=None):
        """
        Validates a NeXus file by walking through its tree structure.
        
        Each group is validated by its corresponding GroupValidator.

        Parameters
        ----------
        path : str, optional
            The path to the group to start validation from (default is
            None, which means the entire file will be validated).

        Returns
        -------
        None
        """
        with nxopen(self.filename) as root:
            if path:
                parent = root[path]
            else:
                parent = root
            for item, indent in self.walk(parent):
                if isinstance(item, NXgroup):
                    validator = get_validator(item.nxclass,
                                              definitions=self.definitions)
                    validator.validate(item, indent=indent)


def validate_file(filename, path=None, definitions=None):
    """
    Validate a NeXus file by walking through its tree structure.

    Parameters
    ----------
    filename : str
        The path to the NeXus file to be validated.
    path : str, optional
        The path to the group to start validation from. Defaults to
        None, which means the entire file will be validated.

    Returns
    -------
    None
    """
    if not Path(filename).exists():
        raise NeXusError(f'File {filename} does not exist')
    validator = FileValidator(filename, definitions=definitions)
    validator.validate(path)


class ApplicationValidator(Validator):

    def __init__(self, application, definitions=None):
        """
        Initializes an instance of the ApplicationValidator class.

        Parameters
        ----------
        application : str
            The name of the application to be validated.
        """
        super().__init__(definitions=definitions)
        self.xml_dict = self.load_application(application)
        
    def load_application(self, application):
        """
        Loads an application definition from an XML file.

        Parameters
        ----------
        application : str, optional
            The name of the application to be loaded. If not provided,
            the application name stored in the instance will be used.

        Returns
        -------
        dict
            A dictionary representation of the application definition.
        """
        if Path(application).exists():
            app_path = Path(application).resolve()
        else:
            app_path = self.application_directory / (f'{application}.nxdl.xml')
        if app_path.exists():
            tree = ET.parse(app_path)
        else:
            raise NeXusError(
                f'The application definition {application} does not exist')
        xml_root = tree.getroot()
        strip_namespace(xml_root)
        if xml_root.tag != 'definition':
            raise NeXusError(
                f'The application definition {application}'
                'does not contain the correct root tag.')
        xml_dict = xml_to_dict(xml_root.find('group'))
        if xml_root.attrib['extends'] != 'NXobject':
            xml_extended_dict = self.load_application(
                xml_root.attrib['extends'])
            xml_dict = merge_dicts(xml_extended_dict, xml_dict)
        return xml_dict

    def validate_group(self, xml_dict, nxgroup, level=0):
        """
        Validates a NeXus group against an XML definition.

        This function checks if the provided NeXus group matches the
        structure defined in the given XML dictionary. It recursively
        validates all subgroups and fields within the group, ensuring
        that the required components are present and correctly
        formatted.

        Parameters
        ----------
        xml_dict : dict
            The XML dictionary containing the definition of the group.
        nxgroup : NXgroup
            The NeXus group to be validated.
        level : int, optional
            The current indentation level (default is 0).
        """
        self.indent = level
        for key, value in xml_dict.items():
            if key == 'group':
                for group in value:
                    if '@minOccurs' in value[group]:
                        minOccurs = int(value[group]['@minOccurs'])
                    else:
                        minOccurs = 1
                    if '@type' in value[group]:
                        name = group
                        group = value[group]['@type']
                        self.log(f'Group: {name}: {group}', level='all')
                    else:
                        name = None
                        self.log(f'Group: {group}', level='all')
                    self.indent += 1
                    nxgroups = nxgroup.component(group)
                    if len(nxgroups) < minOccurs:
                        self.log(
                            f'{len(nxgroups)} {group} group(s) '
                            f'are in the NeXus file.  At least {minOccurs} '
                            'are required', level='error')
                    elif minOccurs == 0:
                        self.log(
                            f'This optional group is not in the NeXus file')
                    for nxsubgroup in nxgroups:
                        if name:
                            self.validate_group(value[name], nxsubgroup,
                                                level=level+1)
                        else:
                            self.validate_group(value[group], nxsubgroup,
                                                level=level+1)
                    self.indent -= 1
                    self.output_log()
            elif key == 'field':
                for field in value:
                    if '@minOccurs' in value[field]:
                        minOccurs = int(value[field]['@minOccurs'])
                    else:
                        minOccurs = 1
                    if field in nxgroup.entries:
                        group_validator = get_validator(
                            nxgroup.nxclass, definitions=self.definitions)
                        field_validator.validate(
                            value[field], nxgroup[field],
                            parent=group_validator, minOccurs=minOccurs,
                            indent=self.indent-1)
                        group_validator.output_log()
                    else:
                        field_path = nxgroup.nxpath + '/' + field
                        self.log(f'Field: {field_path}', level='all')
                        self.indent += 1
                        if minOccurs > 0:
                            self.log(
                                f'This required field is not '
                                'in the NeXus file', level='error')
                        else:
                            self.log(
                                f'This optional field is not '
                                'in the NeXus file')
                        self.indent -= 1
                    self.output_log()
        
    def validate(self, entry):
        """
        Validates a NeXus entry against an XML definition.

        This function checks if the provided NeXus entry matches the
        structure defined in the given XML dictionary. It recursively
        validates all subgroups and fields within the entry, ensuring
        that the required components are present and correctly
        formatted.

        Parameters
        ----------
        entry : object
            The NeXus entry to be validated.
        """
        root = entry.nxroot
        nxpath = entry.nxpath
        self.validate_group(self.xml_dict, root[nxpath])


def validate_application(filename, path=None, application=None,
                         definitions=None):
    """
    Validates a NeXus application definition against a given XML schema.

    Parameters
    ----------
    filename : str
        The name of the NeXus file to be validated.
    path : str, optional
        The path to the NeXus entry to be validated. If not provided,
        the first NXentry group will be used.
    """
    with nxopen(filename) as root:
        if path is None:
            nxpath = root.NXentry[0].nxpath
        else:
            nxpath = path
        entry = root[nxpath]
        if (not isinstance(entry, NXentry)
                and not isinstance(entry, NXsubentry)):
            raise NeXusError(
                f'Path {nxpath} not a NXentry or NXsubentry group')
        elif application is None and 'definition' in entry:
            application = entry['definition'].nxvalue
        elif application is None:
            raise NeXusError(
                f'No application definition defined in {nxpath}')

        validator = ApplicationValidator(application, definitions=definitions)
        validator.validate(entry)


def inspect_base_class(base_class, definitions=None):
    """
    Outputs the base class attributes, groups, and fields.

    Parameters
    ----------
    base_class : str
        The name of the base class to be output.
    """
    validator = get_validator(base_class, definitions=definitions)
    log(f"Base Class: {base_class}")
    if validator.valid_attributes:
        for attribute in validator.valid_attributes:
            log(f"@{attribute}", indent=1)
    if validator.valid_groups:
        log('Allowed Groups', indent=1)
        for group in validator.valid_groups:
            items = {k: v for k, v in validator.valid_groups[group].items()
                     if v != group}
            if '@name' in validator.valid_groups[group]:
                name = validator.valid_groups[group]['@name']
                group = validator.valid_groups[group]['@type']
                attrs = {k: v for k, v in items.items() if v != group
                         and k.startswith('@')}
                log(f"{name}[{group}]: {attrs}", indent=2)
                tags = {k: v for k, v in items.items()
                        if not k.startswith('@')}
                if tags:
                    log(f"{tags}", indent=3)
            else:
                log(f"{group}: {items}", indent=2)
                tags = {k: v for k, v in items.items()
                        if not k.startswith('@')}
                for tag in tags:
                    log(f"{tag}: {tags[tag]}", indent=3)
    if validator.valid_fields:
        log('Defined Fields', indent=1)              
        for field in validator.valid_fields:
            items = {k: v for k, v in validator.valid_fields[field].items()
                     if v != field}
            attrs = {k: v for k, v in items.items() if k.startswith('@')}
            log(f"{field}: {attrs}", indent=2)
            tags = {k: v for k, v in items.items() if not k.startswith('@')}
            for tag in tags:
                log(f"{tag}: {tags[tag]}", indent=3)


def log(message, level='info', indent=0, width=100):
    """
    Logs a message at a specified level with optional indentation.

    Parameters
    ----------
    message : str
        The message to be logged.
    level : str, optional
        The level of the log message (default is 'info').
    indent : int, optional
        The number of spaces to indent the log message (default is 0).
    """
    if len(message) + 4*indent > width:
        message = message[:width - 4*indent - 3] + '...'
    if level == 'info':
        logger.info(f'{4*indent*" "}{message}')
    elif level == 'debug':
        logger.log(logging.DEBUG, f'{4*indent*" "}{message}')
    elif level == 'warning':
        logger.warning(f'{4*indent*" "}{message}')
    elif level == 'error':
        logger.error(f'{4*indent*" "}{message}')
