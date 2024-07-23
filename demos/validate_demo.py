import numpy as np
from nexusformat.nexus import *
import os
import sys
from xml1 import get_valid_entries

filename = 'demos/chopper.nxs'


class GroupValidator():

    def __init__(self, group):
        self.group = group
        self.valid_fields = self.get_valid_fields()
        self.valid_groups = self.get_valid_groups()
        if self.group.nxgroup:
            self.validator = GroupValidator(self.group.nxgroup)
        else:
            self.validator = None

    def get_valid_groups(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file = str(self.group.nxclass) + ".nxdl.xml"
        filepath = os.path.join(current_dir, '..', 'definitions', 'base_classes', file)
        return get_valid_entries(filepath, 'group')

    def get_valid_fields(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file = str(self.group.nxclass) + ".nxdl.xml"
        filepath = os.path.join(current_dir, '..', 'definitions', 'base_classes', file)
        return get_valid_entries(filepath, 'field')

    def validate(self):
        if self.validator is not None:
            if self.group.nxclass in self.validator.valid_groups:
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


def test_validator():

    with nxopen(filename) as root:
        for item in root.walk():
            if isinstance(item, NXgroup):
                validator = GroupValidator(item)
            elif isinstance(item, NXfield):
                validator = FieldValidator(item)
            if validator is not None:
                validator.validate()


if __name__ == "__main__":
    test_validator()
