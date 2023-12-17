THANK YOU FOR RECEIVING TONAL DATA TRANSMISSION ENCODER/DECODER (TDTendec), VERSION 1.12.17
=====
The following text contains full instructions to install and use the TDTendec application programme on your computer.

Installation:
-----
1. First, install the Python application programme on your computer. It is needed to execute the TDTendec's programme.
2. Execute "setup.py" programme to make sure all dependencies are installed.

Usage:
-----
TDTendec can encode and decode files into audio ready to be transmitted. A terminal is required to operate with TDTendec.

To encode the file into the audio:
1. Type in the name of the programme,
2. Type "-e" or "--encode",
3. Type the name of the future AUDIO file
4. Type the name of the DATA file

To decode the audio back to the data file:
1. Type in the name of the programme,
2. Type "-d" or "--decode",
3. Type the name of the AUDIO file
4. Type the name of the future DATA file

IMPORTANT: Don't switch the order, as it will result in an error or file corruption!

Changelog:
-----
1.12.2:
- The first public version.

1.12.3:
- Fixed the bug that made Linux users unable to decode TDT signals.
- Corrected the color gamma.

1.12.17:
- Division frequency now really synchronizes between byte pairs.
- Inability to determine the frequency doesn't make the program go, or rather stop bonkers anymore.
- Its "Read me" file now has a changelog.



(c) 2023 Vyacheslav "VyaCHACHsel" Kirnos, All rights reserved.
Based on "Frequency Shift Keying in Python"
Copyright (c) 2023 Joey Manani
License found at https://cdn.theflyingrat.com/LICENSE.txt
Permission is hereby granted to modify, copy and use this app as per the license WITH credit to me and a link to the license