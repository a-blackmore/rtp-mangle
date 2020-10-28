# rtp-mangle
A Python DICOM-RT Plan "Mangler" for Radiotherapy Quality Assurance

Ever wanted to change your radiotherapy treatment plan in weird and wonderful ways? Well - now you can. With this tool, which is essentially a wrapper to pydicom, you can modify delivery properties to intentionally deliver incorrect treatment plans. This allows you to test the sensitivity of your quality assurance methods, such as diode arrays or in-vivo dosimetry systems. 


# Installation
To run rtp-mangle, first download or clone this repository. To obtain the minimal prerequisite packages, run "pip install pip install -r requirements.txt"


# Usage
The script can be run with the following command:

python mangle.py "input.dcm" -o "output.dcm" "<Command String 1>" "<Command String 2>"

A command string specifies how to edit the RT Plan file - for example, the simplest command string would be "g=0" which will set all control points to deliver at gantry angle 0.

If we wished to confine the edits to only the first beam in the file, we would first specify this, making the command string: "b0 g=0". Perhaps we only wish to edit beams 1 and 3, but not beam 2? "b0,2 g=0" (note the 0 indexing, b2 is the 3rd beam.) We can also specify a range here: "b0-3 g=0". 

Anything more complex might require two command strings - in a plan with 6 beams, we may wish to leave beam 5 alone. "b0-3 g=0" "b5 g=0". 

We can also modify relative to the current value by using either "g=+5" (gantry +5 degrees) or "g+5%". Note that currently, there is no wrap around 360 degrees. 
