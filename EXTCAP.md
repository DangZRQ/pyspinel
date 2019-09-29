#Spinel Extcap Reference
The Spinel Extcap provides a more user-friendly way to use OpenThread Sniffer. Spinel 
Extcap is primarily targeted for integrating OpenThread Sniffer with Wiresahrk,  and 
is suitable for user to use OpenThread Sniffer by Wireshark GUI.

## System Requirements

The tool has been tested on the following platforms:

| Platforms  | Version          |
|------------|------------------|
| Ubuntu     | 14.04 Trusty     |
| Mac OS     | 10.11 El Capitan |
| Windows 10 | 1803             |

| Language  | Version          |
|-----------|------------------|
| Python    | 2.7.10           |

| Software  | Version          |
|-----------|------------------|
| Wireshark | 3.0.3            |

### Package Installation
#### Automatic installation from source
```
git clone https://github.com/openthread/pyspinel
cd pyspinel
sudo python setup.py install 
```
#### Automatic install from PYPI (pending for new release package)
```
pip install pyspinel
```
#### Manual installation(for pyspinel 1.0.0a3 and before)
**1. Install pyspinel package**
``` 
pip install pyspinel 
```
**2. Install extcap script on Wireshark**

To find the correct installation path of the extcap utility on any system please open Wireshark:
```
"Help" -> "About Wireshark" -> "Folders" -> "Extcap path"
```
Copy the provided ```extcap_ot.py```, ```extcap_ot.bat``` and ```sniffer.py``` to the extcap directory.

For OS X and Linux, verify that the ```extcap_ot.py``` file has the “x” permission. If not, add it using:

```
chmod +x extcap_ot.py
```

For Windows, verify that the ```extcap_ot.bat``` file is in the extcap folder

## Usage

### NAME
    extcap_ot.py - external script for integrating OpenThread Sniffer with Wireshark

### SYNOPSIS
    extcap_ot.py [--arguments]

### DESCRIPTION

```
    -h, --help            
    	Show this help message and exit

    --extcap-interfaces
       	Provide a list of interfaces to capture from.

    --extcap-interface <EXTCAP_INTERFACE>
        Provide the interface to capture from.
    
    --extcap-dlts
        Provide a list of dlts for the given interface

    --extcap-config
        Provide a list of configurations for the given interface.

    --fifo <FIFO>
        Use together with capture to provide the fifo to dump data to.
    
    --channel <CHANNEL>
         IEEE 802.15.4 capture channel [11-26].

    --baudrate <BAUDRATE>
        Set the serial port baud rate.

    --tap
        Use to specify DLTs as IEEE 802.15.4 TAP (only for Wireshark3.0 and later).
```

## Quick Start
### Configuring Wireshark for Thread
* Wireshark configuration - [Protocols](https://openthread.io/guides/ncp/sniffer#wireshark_configuration_-_protocols)
* Wireshark configuration - [FCS Format](https://openthread.io/guides/ncp/sniffer#wireshark_configuration_-_rssi)
    *  For Wireshark 2.x: TI CC24xx metadata
    * For Wireshark 3.x: ITU-T CRC-16
   
### Using the Sniffer
#### Wireshark capture screen
The Wireshark capture screen is displayed when Wireshark is first launched. 
It includes the Wireshark interface for managing packets that are captured 
and the hardware interfaces connected to the OT Sniffer.
#### Start sniffing

There are three ways to start sniffing:
* If this is your first time using an interface, click on interface options 
  to set channel and baudrate, then click start. Check the IEEE 802.15.4 tap 
  to ensure that the channel information is included in the pcap output and 
  can be displayed in the Wireshark GUI. The parameters will be saved after 
  the start of the capture, and you will not need to set it again the next 
  time you use the interface (unless you need to change the channel)

* Double click on the hardware interface
* Select the hardware interface by clicking on it and then click the Wireshark 
  icon on the top left to start sniffing.
 
 #### Capture from multiple hardware interfaces/boards
 Select all hardware interfaces in the Capture Screen in Wireshark and click 
 the Wireshark icon on the top left to start sniffing.
 
**Interface ID (frame.interface_id)**\
Interface Identifier used by Wireshark to identify the capture interfaces

**Interface name (frame.interface_name)**\
Interface Identifier used by Wireshark to identify the capture interfaces 

**Channel (wpan-tap.ch_num)**

## Troubleshooting
### The OT sniffer is not listed in the Wireshark interface. 
1. If you have multiple Python interpreters installed, ensure that Python2 interpreter is used by the extcap script. The sniffer.py doesn't support python3 yet.
2. See if the hardware has been enumerated on USB and the drivers are loaded. 
3. Check that the HEX file for the hardware has been flashed. 
4. Reset the hardware by unplugging the hardware, waiting 5 seconds, and plugging it back in. 
5. Restart Wireshark. If it still doesn’t appear, verify the python script located in the extcap folder is able to run. 
    
    For OS X and Linux:
    1. Verify that the execute permission is present for the extcap_ot.py file. 
        ```
       ls -l extcap_ot.py
        ```
    2. If the "x" permission is missing:
       ```
       chmod +x extcap_ot.py
       ```
    3. Run ```python extcap_ot.py --extcap-interfaces``` to list the interface
    
    For Windows:
    1. Run ```extcap_ot.bat --extcap-interfaces``` to list the interface.
    2. If this exits with a python error, verify that python.exe can be run from the command line ```C:>python.exe --version```
#### Wireshark only allow the root user to capture packets
During the Wireshark installation on Ubuntu the user will be prompted to choose one of the following options:
* Create the wireshark user group and allow all members of that group to capture packets.
* Only allow the root user to capture packets.

**Note**: Using the Wireshark as the root user is strongly discouraged.

To change the settings after the installation, run the following command:
```
sudo dpkg-reconfigure wireshark-common
```
If the Wireshark was configured to restrict the capture to members of the wireshark group, add the correct user to the group:
```
sudo usermod -a -G wireshark [user]
```

Add the correct user to the dialout group:
```
sudo usermod -a -G dialout [user]
```
Log-out and log-in again to apply the new user group settings.

#### Wireshark format error when capturing on multiple USB interfaces on windows
It's related to a Wireshark [bug](https://bugs.wireshark.org/bugzilla/show_bug.cgi?id=13653), 
and a patch has been provided. Please download the [patch](Please download the patch and recompile Wireshark)
and recompile Wireshark.