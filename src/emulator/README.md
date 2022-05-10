# MTP emulator

## For testing the MTP control program ctrl/view.py
To run the MTP instrument emulator, start the emulator and note the lines it returns:

```
> python3 mtp_emulator.py [--debug]
Emulator connecting to virtual serial port: /var/folders/ph/6ph43gj971lfy2qn4r4p7_vw000244/T/tmp46e5rvbk/mtpport
User clients connect to virtual serial port: /var/folders/ph/6ph43gj971lfy2qn4r4p7_vw000244/T/tmp46e5rvbk/userport
```

You will not get the command prompt back. Leave this window open. Then in another window start ctrl/view.py with the userport as a command line option:

```
python3 view.py --mtph Config.mtph --device=/var/folders/ph/6ph43gj971lfy2qn4r4p7_vw000244/T/tmp46e5rvbk/userport
```

The control code window should launch, initialize, and start cycling through the view angles.

## For testing MTPviewer
To emulate real-time conditions receiving IWG packets and MTP data over UDP on
the airplane, start snd_IWG.sh in one window:

```
./snd_IWG.sh
```

and when it gets to 20140606T062252, start send_MTP_udp.py

```
python3 snd_MTP_udp.py
```
