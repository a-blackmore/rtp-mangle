#!/usr/bin/env python

"""mangle.py: Modifies a DICOM-RT Plan File to create intentional delivery errors."""

# Imports
import argparse
import shlex
import re
import pydicom
from pydicom.uid import generate_uid

"""
Parse Command Line Arguments
----------------------------

Uses argparse - https://docs.python.org/3/library/argparse.html

"""

parser = argparse.ArgumentParser(description='Modify a DICOM-RT Plan File to Add Delivery Errors.')
parser.add_argument('inFile',                   # Use strings for filenames rather than file objects,
    type=str,                                   # allows pydicom to handle the file operations.
    help='DICOM-RT Plan to Modify.')
parser.add_argument("-v", "--verbose",
    help="increase output verbosity",
    action="store_true")
parser.add_argument("-k", "--keep_uid",
    help="Keep Original Instance UID",
    action="store_true")
parser.add_argument('-o', '--outFile',
    type=str,
    default="out.dcm",
    help='Output File to create.',
    nargs='?',)
parser.add_argument('commandString',
    type=str,
    help='A Mangle command string describing how to alter the file. See documentation for details.',
    nargs='+',)
args = parser.parse_args()


"""
Parse the Command Strings
-------------------------

See wiki documentation for full instructions. The command strings instruct the script on how to
edit the RTPlan. They consist of two types: filters and setters.

Filters specify what needs to be edited; the specific beams and control points within the file. The
intention is to ultimately be able to finely filter, by gantry angle for example, or CPs with less than
a certain MU.

Setters are the methods through which we change the file. Parameters can either be specified exactly,
or they can be relative, such as +x% or +y units.

The first step in parsing the command strings is to gather the required data into an easily accessible form
using the filters.

"""

# Open DICOM File in pydicom and retrieve a dataset:
ds = pydicom.dcmread(args.inFile)

# Unless Instructed, change the file's UID to prevent duplicates. 
if not args.keep_uid:
    ds.SOPInstanceUID = generate_uid()

# Parse Command Strings
if args.verbose:
    print("Found " + str(len(args.commandString)) + " command string(s)." )

for cmdStr in args.commandString:
    if args.verbose:
        print("\nProcessing Command String: " + cmdStr + "\n" )
    
    # Prevent Simultaneous Jaw and MLC editing.
    if "lp" in cmdStr or "lb" in cmdStr:
        if "jb" in cmdStr or "j" in cmdStr:
            print("ERROR: Cannot Edit Leaf and Jaw positions in the same command.\n")
            raise ValueError

    # Prevent Simultaneous Relative and Absoulte edits.
    if "pr=" in cmdStr and "pa=" in cmdStr:
        print("ERROR: Cannot Edit Relative and Absolute positions in the same command.\n")
        raise ValueError

    cmds = shlex.split(cmdStr)

    filters = []
    beams = []
    cps = []
    pairs = []

    filters.append({"name": "beam",        "key": "b",   "default": "*", "matches": ""})
    filters.append({"name": "control pt",  "key": "cp",  "default": "*", "matches": ""})
    filters.append({"name": "jaw",         "key": "j",   "default": "*", "matches": ""})
    filters.append({"name": "jaw bank",    "key": "jb",  "default": "*", "matches": ""})
    filters.append({"name": "leaf pair",   "key": "lp",  "default": "*", "matches": ""})
    filters.append({"name": "leaf bank",   "key": "lb",  "default": "*", "matches": ""})

    for f in filters:
        
        r = re.compile("(^" + f["key"] + "\d+)")
        reArgs = list(filter(r.match, cmds))

        if len(reArgs) > 1:
            # More than one fstring.
            print("ERROR: More than one " + f["name"] + " filter found.\n")
            raise ValueError
        elif len(reArgs) < 1:
            reArgs = [f['key'] + f["default"]]

        # Remove the key from the command
        reArgs = reArgs[0][len(f["key"]):]
                
        if args.verbose and reArgs != f["default"]:
            print("Found " + f["name"] + " filter - Value: " + reArgs)

        # Handle Multiple Specified Values
        reArgs = reArgs.split(",")

        # Handle Range of Values
        for i in reArgs:
            if "-" in i:
                reArgs.remove(i)
                for j in range(int(i.split("-")[0]), int(i.split("-")[1])+1):
                    reArgs.append(str(j))

        f["matches"] = reArgs

        # Gather the data to act upon
        if f["name"] == "beam": # Build the Beam list.
            if f["matches"][0] == "*":
                beams = ds.BeamSequence
            else:
                for i in f["matches"]:
                    try:
                        beams.append(ds.BeamSequence[int(i)])
                    except IndexError:
                        print("WARNING: Beam Index Out of Plan Range - Ignoring beam " + i + ".\n")
        elif f["name"] == "control pt": # Build the CP list.
            if f["matches"][0] == "*":
                for beam in beams:
                    for cp in beam.ControlPointSequence:
                        cps.append(cp)
            else:
                for beam in beams:
                    for i in f["matches"]:
                        try:
                            cps.append(beam.ControlPointSequence[int(i)])
                        except IndexError:
                            print("WARNING: Control Point Index Out of Beam Range - Ignoring CP " + i + ".\n")
        elif f["name"] == "jaw" or f["name"] == "jaw bank" or f["name"] == "leaf bank":
            if f["matches"][0] == "*":
                f["matches"] = list(range(0, 2))

        elif f["name"] == "leaf pair":
                maxPairs = 0
                for bld in beams[0].BeamLimitingDeviceSequence:
                    if bld.RTBeamLimitingDeviceType == "MLCX" or bld.RTBeamLimitingDeviceType == "MLCY":
                        if int(bld.NumberOfLeafJawPairs) > maxPairs:
                            maxPairs = bld.NumberOfLeafJawPairs
                if f["matches"][0] == "*":
                    f["matches"] = list(range(0, maxPairs))


    """
    Perform the edits

    Now we have gathered the items to be edited, we can start looking at the setters.

    """

    # Perform Edits
    setters = []
    setters.append({"name": "MU",                  "type": "int",   "key": "mu="})
    setters.append({"name": "Machine",             "type": "str",   "key": "m="})
    setters.append({"name": "Gantry",              "type": "int",   "key": "g=",     "attr": "GantryAngle"})
    setters.append({"name": "Collimator",          "type": "int",   "key": "c=",     "attr": "BeamLimitingDeviceAngle"})
    setters.append({"name": "Position Absolute",   "type": "int",   "key": "pa=",    "attr": "BeamLimitingDevicePositionSequence"})
    setters.append({"name": "Position Relative",   "type": "int",   "key": "pr=",    "attr": "BeamLimitingDevicePositionSequence"})
    
    for s in setters:

        if s["type"] == "int":
            r = re.compile("(" + s["key"] + "[+-]?\d+%?)")
        else:
            r = re.compile("(" + s["key"] + "[\']?[a-zA-Z0-9\ ]+[\']?)")
            
        reArgs = list(filter(r.match, cmds))

        if len(reArgs) > 1:
            # More than one fstring.
            print("ERROR: More than one " + s["name"] + " set command found.\n")
            raise ValueError
        elif len(reArgs) != 1:
            continue

        # Remove the key from the command
        reArg = reArgs[0][len(s["key"]):]
        
        if args.verbose:
            print("Found " + s["name"] + " setter - Value: " + reArg)

        if s["name"] == "MU":
            for beam in beams:
                cmdArg = reArg
                meterset = ds.FractionGroupSequence[0].ReferencedBeamSequence[beam.BeamNumber - 1].BeamMeterset
                if cmdArg[0] == "+":
                    cmdArg = cmdArg[1:]
                    if cmdArg[-1] == "%":
                        cmdArg = cmdArg[:-1]
                        ds.FractionGroupSequence[0].ReferencedBeamSequence[beam.BeamNumber - 1].BeamMeterset = meterset * (1+(float(cmdArg)/100))
                    else:
                        meterset = meterset + cmdArg
                elif cmdArg[0] == "-":
                    cmdArg = cmdArg[1:]
                    if cmdArg[-1] == "%":
                        cmdArg = cmdArg[:-1]
                        ds.FractionGroupSequence[0].ReferencedBeamSequence[beam.BeamNumber - 1].BeamMeterset = meterset * (1-(float(cmdArg)/100))
                    else:
                        ds.FractionGroupSequence[0].ReferencedBeamSequence[beam.BeamNumber - 1].BeamMeterset = meterset - cmdArg
                else:
                     meterset = cmdArg
        elif s["name"] == "Machine":
            for beam in beams:
                cmdArg = reArg
                beam.TreatmentMachineName = cmdArg
        else:
            for cp in cps:
                cmdArg = reArg
                if hasattr(cp, s["attr"]):
                    # Handle Jaw/MLC Changes
                    if s['name'] == "Position Absolute" or s['name'] == "Position Relative":
                        if "lp" in cmdStr or "lb" in cmdStr:
                            # MLCs
                            lb = [lb["matches"] for lb in filters if lb['name'] == 'leaf bank']
                            lp = [lp["matches"] for lp in filters if lp['name'] == 'leaf pair']

                            for bld in cp.BeamLimitingDevicePositionSequence:
                                if bld.RTBeamLimitingDeviceType == "MLCX" or bld.RTBeamLimitingDeviceType == "MLCY":
                                    banks = []
                                    banks.append(bld.LeafJawPositions[:maxPairs])
                                    banks.append(bld.LeafJawPositions[maxPairs:])

                                    for bank in lb:
                                        for pair in lp:
                                            if s['name'] == "Position Absolute":
                                                banks[bank][pair] = cmdArg
                                            elif s['name'] == "Position Relative":
                                                pass

                                    bld.LeafJawPositions = banks[0] + banks[1]

                        elif "jb" in cmdStr or "j" in cmdStr:
                            # Jaws
                            jb = [jb["matches"] for jb in filters if jb['name'] == 'jaw bank'][0]
                            j =  [j["matches"]  for j  in filters if j['name']  == 'jaw'][0]

                            target = ""
                            for jaw in j:
                                if int(jaw) == 0:
                                    target = "ASYMX"
                                elif int(jaw) == 1:
                                    target = "ASYMY"

                                for bld in cp.BeamLimitingDevicePositionSequence:
                                    if bld.RTBeamLimitingDeviceType == target:
                                        for bank in jb:
                                            if s['name'] == "Position Absolute":
                                                bld.LeafJawPositions[int(bank)] = cmdArg
                                            elif s['name'] == "Position Relative":
                                                pass

                    # Handle Gantry/Collimator Changes
                    elif cmdArg[0] == "+":
                        cmdArg = cmdArg[1:]
                        if cmdArg[-1] == "%":
                            cmdArg = cmdArg[:-1]
                            exec("cp." + s["attr"] + "= (cp." + s["attr"] + " * (1 + (" + cmdArg + "/100))")
                        else:
                            exec("cp." + s["attr"] + "= (cp." + s["attr"] + " + " + cmdArg + ")")
                    elif cmdArg[0] == "-":
                        cmdArg = cmdArg[1:]
                        if cmdArg[-1] == "%":
                            cmdArg = cmdArg[:-1]
                            exec("cp." + s["attr"] + "= (cp." + s["attr"] + " * (1 - (" + cmdArg + "/100))")
                        else:
                            exec("cp." + s["attr"] + "= (cp." + s["attr"] + " - " + cmdArg + ")")
                    else:
                        exec("cp." + s["attr"] + "=" + cmdArg)

"""
Write the output file.
"""

ds.save_as(args.outFile)
print("Output File " + args.outFile + " created.")
