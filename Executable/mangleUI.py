#!/usr/bin/env python

"""mangle.py: Modifies a DICOM-RT Plan File to create intentional delivery errors."""

# Imports
import shlex
import re
import pydicom
from pydicom.uid import generate_uid


def mangle(inFile, outFile, keep_uid, verbose, commandString):

    # Open DICOM File in pydicom and retrieve a dataset:
    ds = pydicom.dcmread(inFile)

    # Unless Instructed, change the file's UID to prevent duplicates. 
    if not keep_uid:
        ds.SOPInstanceUID = generate_uid()

    # Parse Command Strings
    if verbose:
        print("Found " + str(len(commandString)) + " command string(s)." )
    for cmdStr in commandString:
        if verbose:
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
                    
            if verbose and reArgs != f["default"]:
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
            
            if verbose:
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
                            ds.FractionGroupSequence[0].ReferencedBeamSequence[beam.BeamNumber - 1].BeamMeterset = meterset + float(cmdArg)
                    elif cmdArg[0] == "-":
                        cmdArg = cmdArg[1:]
                        if cmdArg[-1] == "%":
                            cmdArg = cmdArg[:-1]
                            ds.FractionGroupSequence[0].ReferencedBeamSequence[beam.BeamNumber - 1].BeamMeterset = meterset * (1-(float(cmdArg)/100))
                        else:
                            ds.FractionGroupSequence[0].ReferencedBeamSequence[beam.BeamNumber - 1].BeamMeterset = meterset - float(cmdArg)
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
                                
                                # Collect the list of Leaf Banks and Leaf Pairs that must be edited.
                                lb = [lb["matches"] for lb in filters if lb['name'] == 'leaf bank'][0]
                                lp = [lp["matches"] for lp in filters if lp['name'] == 'leaf pair'][0]
                                lb = [int(i) for i in lb] 
                                lp = [int(i) for i in lp] 

                                # Cycle Through the BLD Sequences in the control point. Look for "MLCX" or "MLCY" - Note that futuristic machines with both MLCX and MLCY won't work!
                                for bld in cp.BeamLimitingDevicePositionSequence:
                                    if bld.RTBeamLimitingDeviceType == "MLCX" or bld.RTBeamLimitingDeviceType == "MLCY":
                                        # Split the Banks up - DICOM stores the MLCs in one long list. 
                                        banks = []
                                        banks.append(bld.LeafJawPositions[:maxPairs])
                                        banks.append(bld.LeafJawPositions[maxPairs:])
                                        
                                        # For each bank
                                        for bank in lb:
                                            bank = int(bank)
                                            if s['name'] == "Position Absolute":
                                                for pair in lp:
                                                    # Absolute Position Specified. Set each of the pairs to modify in this bank to that value. 
                                                    banks[bank][pair] = cmdArg
                                            elif s['name'] == "Position Relative":
                                                if cmdArg[0] == "-":
                                                    cmdArgV = cmdArg[1:]
                                                    if cmdArg[-1] == "%":
                                                        cmdArgV = cmdArgV[:-1]
                                                        for pair in lp:
                                                            # Negative Percentage Relative Edit. Decrement the existing value by x%.
                                                            banks[bank][pair] = float(banks[bank][pair]) * (1 - (float(cmdArgV)/100))
                                                    else:
                                                        for pair in lp:
                                                            # Negative Relative Edit. Decrease the exisiting value.
                                                            banks[bank][pair] = float(banks[bank][pair]) - float(cmdArgV)
                                                else:
                                                    cmdArgV = cmdArg
                                                    if cmdArg[0] == "+":
                                                        cmdArgV = cmdArg[1:]
                                                    if cmdArg[-1] == "%":
                                                        cmdArgV = cmdArgV[:-1]
                                                        for pair in lp:
                                                            # Positive Percentage Relative Edit. Increment the existing value by x%.
                                                            banks[bank][pair] = float(banks[bank][pair]) * (1 + (float(cmdArgV)/100))
                                                    else:
                                                        for pair in lp:
                                                            # Positive Relative Edit. Increase the exisiting value.
                                                            banks[bank][pair] = float(banks[bank][pair]) + float(cmdArgV)
                                                

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
                                                    if cmdArg[0] == "-":
                                                        cmdArgV = cmdArg[1:]
                                                        if cmdArg[-1] == "%":
                                                            cmdArgV = cmdArgV[:-1]
                                                            # Negative Percentage Relative Edit. Decrement the existing value by x%.
                                                            bld.LeafJawPositions[int(bank)] = bld.LeafJawPositions[int(bank)] * (1 - (float(cmdArgV)/100))
                                                        else:
                                                            # Negative Relative Edit. Increase the exisiting value.
                                                            bld.LeafJawPositions[int(bank)] = bld.LeafJawPositions[int(bank)] - float(cmdArgV)
                                                    else: 
                                                        cmdArgV = cmdArg
                                                        if cmdArg[0] == "+":
                                                            cmdArgV = cmdArg[1:]                                       
                                                        if cmdArg[-1] == "%":
                                                            cmdArgV = cmdArgV[:-1]
                                                            # Positive Percentage Relative Edit. Increment the existing value by x%.
                                                            bld.LeafJawPositions[int(bank)] = bld.LeafJawPositions[int(bank)] * (1 + (float(cmdArgV)/100))
                                                        else:
                                                            # Positive Relative Edit. Increase the exisiting value.
                                                            bld.LeafJawPositions[int(bank)] = bld.LeafJawPositions[int(bank)] + float(cmdArgV)

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

    ds.save_as(outFile)
    print("Output File " + outFile + " created.")
