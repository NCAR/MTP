This directory holds unit tests for the MTP code.

On a MAC/LINUX, type:
```
> cd src/
OR
> cd tests/
THEN
> python3 -m unittest discover -s ../tests -v
```

To run them on a WINDOWS10, type:
```
> cd src\
OR
> cd tests\
THEN
> python -m unittest discover -s ..\tests
OR
> python -m unittest discover ..\tests -v -p test_name_here.py
OR
> powershell -noexit "& ""..\tests\run_tests_Windows.ps1"""
```
