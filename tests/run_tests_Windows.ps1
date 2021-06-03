# This is a powershell script that runs all of the unittests (as of 5/20/21) individually to avoid memory errors
# To run it, do & C:file\location\run_tests_Windows.ps1
# This may not be a complete list if more tests are added later!

python -m unittest discover -s ..\tests -v -p test_1messageHandler.py
python -m unittest discover -s ..\tests -v -p test_calcTB.py
python -m unittest discover -s ..\tests -v -p test_eng1.py
python -m unittest discover -s ..\tests -v -p test_eng2.py
python -m unittest discover -s ..\tests -v -p test_eng3.py
python -m unittest discover -s ..\tests -v -p test_icartt.py
python -m unittest discover -s ..\tests -v -p test_iwg.py
python -m unittest discover -s ..\tests -v -p test_MTPclient.py
python -m unittest discover -s ..\tests -v -p test_MTPprocessor.py
python -m unittest discover -s ..\tests -v -p test_MTPviewer.py
python -m unittest discover -s ..\tests -v -p test_MTPviewer2.py
python -m unittest discover -s ..\tests -v -p test_quit.py
python -m unittest discover -s ..\tests -v -p test_rcf_set.py
python -m unittest discover -s ..\tests -v -p test_rcf.py
python -m unittest discover -s ..\tests -v -p test_readascii_parms.py
python -m unittest discover -s ..\tests -v -p test_readGVnc.py
python -m unittest discover -s ..\tests -v -p test_readmtp.py
python -m unittest discover -s ..\tests -v -p test_retriever.py
python -m unittest discover -s ..\tests -v -p test_tempresist.py
python -m unittest discover -s ..\tests -v -p test_tropopause.py
python -m unittest discover -s ..\tests -v -p test_udp.py