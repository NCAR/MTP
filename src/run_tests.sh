###############################################################################
# Run this script to run unit tests where memory is an issue.
#
# I am running into a problem running out of memory when I run these tests on
# my MAC - I don't have this problem on the Windows10 machines. Python's
# unittest holds on to all sorts of memory until the entire test suite has been
# run. For a good explanation see:
#
# https://stackoverflow.com/questions/26915115/unittest-teardown-del-all-attributes/35001389
#
# To get around this, run the test_eng tests separately (since they are
# currently the biggest culprits), eg instead of running
# python3 -m unittest discover -s ../tests -v
# add a -k to pattern match on which test files to run:
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2020
###############################################################################
python3 -m unittest discover -s ../tests -v -k test_[0-9A-Za-df-z]
python3 -m unittest discover -s ../tests -v -k test_eng1
python3 -m unittest discover -s ../tests -v -k test_eng2
python3 -m unittest discover -s ../tests -v -k test_eng3
