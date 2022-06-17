###############################################################################
# Run this script to run unit tests
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2020
###############################################################################
cd ../src
python3 -m unittest discover -s ../tests -v -p "test_pointing.py"
