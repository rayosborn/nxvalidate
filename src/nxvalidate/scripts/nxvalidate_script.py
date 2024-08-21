#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Copyright (c) 2024, Kaitlyn Marlor, Ray Osborn, Justin Wozniak.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------

import argparse
import logging
import xml.etree.ElementTree as ET

from nxvalidate.validate import logger, report, validate_application, validate_file


def main():
    parser = argparse.ArgumentParser(
        prog="nxvalidate",
        description="Validates NeXus files.")
    parser.add_argument("-f", "--filename", nargs = 1,
                        help="name of the NeXus file to be validated")
    parser.add_argument("-p", "--path", nargs = 1,
                        help = "path to group to be validated in the NeXus file")
    parser.add_argument("-a", "--application", nargs = '?',
                        help = "name of the application used to validate the NeXus file")
    parser.add_argument("-b", "--baseclass", nargs = 1,
                        help = "name of the base class to be listed")
    parser.add_argument("-i", "--info", action='store_true',
                        help = "Output info messages in addition to warnings and errors")
    parser.add_argument("-d", "--debug", action='store_true',
                        help = "Output info messages in addition to warnings and errors")
    parser.add_argument("-w", "--warning", action='store_true',
                        help = "Output info messages in addition to warnings and errors")
    parser.add_argument("-e", "--error", action='store_true',
                        help = "Output info messages in addition to warnings and errors")
    args = parser.parse_args()

    if args.info or args.baseclass:
        logger.setLevel(logging.INFO)
    elif args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.warning:
        logger.setLevel(logging.WARNING)
    elif args.error:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.WARNING)

    if args.baseclass:
        report(args.baseclass[0])
    elif args.filename:
        if args.path:
            if args.application:
                validate_application(args.filename[0], args.application[0], args.path[0])
            else:
                validate_file(args.filename[0], args.path[0])
        else:
            validate_file(args.filename[0])


if __name__ == "__main__":
    main()
