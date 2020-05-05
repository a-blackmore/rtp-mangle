#!/usr/bin/env python

"""mangle.py: Modifies a DICOM-RT Plan File to create intentional delivery errors."""

# Imports
import argparse
import pydicom
import re

# Parse Command Line Arguments
parser = argparse.ArgumentParser(description='Modify a DICOM-RT Plan File to Add Delivery Errors.')
parser.add_argument('in-file',
    type=argparse.FileType('r'),
    help='DICOM-RT Plan to Modify.')
parser.add_argument('-o', '--out-file',
    type=argparse.FileType('wb', 0),
    default="out.dcm",
    help='Output File to create.',
    nargs='?',)
parser.add_argument('commandString',
    type=str,
    help='A Mangle command string describing how to alter the file.',
    nargs='+',)
args = parser.parse_args()
print(args.commandString)

# Parse Command Strings

# Perform Plan Edits

# Output
