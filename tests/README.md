This directory will hold unit tests for the MTP code. To run them on a MAC/LINUX, type:

```
cd src/
python3 -m unittest discover -s ../tests -v
```

To run them on a WINDOWS10, type:

```
python -m unittest discover -s ..\tests
OR
python -m unittest discover ..\tests -v -p test_name_here.py
OR
powershell -noexit "& ""C:\...\MTP\tests\run_tests_Windows.ps1"""
```
