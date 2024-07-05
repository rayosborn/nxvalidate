#!/usr/bin/env python

"""
NXVALIDATE PY
"""

import logging
import os
import sys

import xml.etree.ElementTree as ET


def main():
    """ Outline of program """
    logger = logging.getLogger("nxvalidate")
    setup_logger(logger)
    logger.info("NXVALIDATE")
    settings = load_defaults()
    args = parse_args()
    apply_args(logger, args, settings)
    try:
        do_command(logger, args, settings)
    except UserError as e:
        print("nxvalidate: user error: " + " ".join(e.args))
        exit(1)


class UserError(Exception):
    """ Generic user error for the nxvalidate program. """
    pass


def setup_logger(logger):
    """ Set up the logger for development use """
    logger.setLevel(logging.DEBUG)
    h = logging.StreamHandler(stream=sys.stdout)
    fmtr = logging.Formatter(
            "%(asctime)s %(name)s %(levelname)-5s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
    h.setFormatter(fmtr)
    logger.addHandler(h)
    return logger


def load_defaults():
    """ Set up default settings from environment """
    settings = {}
    settings["definitions"] = env_default("NEXUS_DEFINITIONS")
    return settings


def env_default(name, default=None):
    """ Helper function to deal with environment variables """
    result = None
    value = os.getenv(name)
    if value is not None and len(value) > 0:
        result = value
    return result


def parse_args():
    """
    Use argparse to handle command line
    Probably should match and extend cnxvalidate for sanity
    """
    import argparse
    parser = argparse.ArgumentParser(
        prog="nxvalidate",
        description="Validates NXS files.")
    parser.add_argument("-l",
                        action="store",
                        help="application definition directory")
    parser.add_argument("command",
                        help="one of: 'report' or ...")
    parser.add_argument("extras", nargs="*",
                        help="Additional arguments")
    args = parser.parse_args()
    return args


def apply_args(logger, args, settings):
    if "l" in args:
        settings["definitions"] = args.l


def do_command(logger, args, settings):
    if args.command == "report":
        do_report(logger, args, settings)
    # TODO: Add other commands here


def do_report(logger, args, settings):
    """ Execute the report """
    logger.info("do_report...")
    if len(args.extras) != 1:
        raise UserError("report requires 1 token!")
    token = args.extras[0]
    logger.debug("requested: '%s'" % token)
    base_classes = get_base_classes(settings)
    xml_file = base_classes + "/" + token + ".nxdl.xml"
    logger.debug("open: " + xml_file)
    try:
        with open(xml_file) as fp:
            report_items(fp, token)
    except FileNotFoundError as e:
        print(str(e.__dir__()))
        raise UserError("could not open XML definition: " +
                        e.filename)


def report_items(fp, token):
    # Parse the XML:
    tree = ET.parse(fp)
    root = tree.getroot()
    # Lookup some header metadata
    extends = root.attrib["extends"]
    print("%s extends %s" % (token, extends))
    # These will be our "rules":
    groups = []
    attributes = []
    fields = []
    # Scan through the XML tree for entries about our rules:
    for child in root:
        tag = get_tail(child.tag)
        if tag == "group":
            groups.append(child.attrib["type"])
        elif tag == "attribute":
            attributes.append(child.attrib["name"])
        elif tag == "field":
            fields.append(child.attrib["name"])
    # Report groups:
    print("%s may contain these %i groups:" %
          (token, len(groups)))
    for group in groups:
        print("\t " + group)
    # Report attributes:
    print("%s may contain these %i attributes:" %
          (token, len(attributes)))
    for attribute in attributes:
        print("\t " + attribute)
    # Report fields:
    print("%s may contain these %i fields:" %
          (token, len(fields)))
    for field in fields:
        print("\t " + field)


def get_base_classes(settings):
    """ Find the directory named base_classes """
    if settings["definitions"] is None:
        raise UserError("application definition directory " +
                        "not specified!")
    p = settings["definitions"] + "/../base_classes"
    base_classes = os.path.abspath(p)
    return base_classes


def get_tail(s):
    """ Remove the namespace portion from the XML tag """
    tokens = s.split("}")
    return tokens[1]


if __name__ == "__main__":
    main()
