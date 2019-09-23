#! /usr/bin/env python

from __future__ import print_function
import os
import sys
import argparse
import subprocess
import threading

from spinel.stream import StreamOpen
from spinel.const import SPINEL
from spinel.codec import WpanApi
from serial.tools.list_ports import comports
from enum import Enum

# Nodeid is required to execute ot-ncp-ftd for its sim radio socket port.
# This is maximum that works for MacOS.
DEFAULT_NODEID = 34
COMMON_BAUDRATE = [460800, 115200, 9600]

class CONFIG(Enum):
    CHANNEL = 0
    BAUDRATE = 1
    TAP = 2

def extcap_config(interface, option):
    """List configuration for the given interface"""
    args = []
    values = []
    args.append((CONFIG.CHANNEL.value, '--channel', 'Channel', 'IEEE 802.15.4 channel', 'selector', '{required=true}{default=11}'))
    args.append((CONFIG.BAUDRATE.value, '--baudrate', 'Baudrate', 'Serial port baud rate', 'selector', '{required=true}{default=460800}'))
    args.append((CONFIG.TAP.value, '--tap', 'IEEE 802.15.4 TAP (only for Wireshark3.0 and later)', 'IEEE 802.15.4 TAP', 'boolflag', '{default=yes}'))

    for arg in args:
        print("arg {number=%d}{call=%s}{display=%s}{tooltip=%s}{type=%s}%s" % arg)

    values = values + [(CONFIG.CHANNEL.value, "%d" % i, "%d" % i, "true" if i == 11 else "false") for i in range(11, 27)]
    values = values + [(CONFIG.BAUDRATE.value, "%d" % b, "%d" % b, "true" if b == 115200 else "false") for b in COMMON_BAUDRATE]

    for value in values:
        print("value {arg=%d}{value=%s}{display=%s}{default=%s}" % value)

def extcap_dlts(interface):
    """List DLTs for the given interface"""
    print("dlt {number=195}{name=IEEE802_15_4_WITHFCS}{display=IEEE 802.15.4 with FCS}")
    print("dlt {number=283}{name=IEEE802_15_4_TAP}{display=IEEE 802.15.4 TAP}")

def serialopen(interface, __console__, DirtylogFile):
    """
    Open serial to indentify OpenThread sniffer
    :param interface: string, eg: "/dev/ttyUSB0 - Zolertia Firefly platform", "/dev/ttyACM1 - nRF52840 OpenThread Device"
    """
    sys.stdout = DirtylogFile
    interface = str(interface).split()[0]

    stream = StreamOpen('u', interface, False)
    wpan_api = WpanApi(stream, nodeid=DEFAULT_NODEID)
    value = wpan_api.prop_get_value(SPINEL.PROP_CAPS)

    if value is not None:
        sys.stdout = __console__
        if sys.platform == 'win32':
            # The wireshark will show interfaces as "OpenThread Sniffer" rather than "OpenThread Sniffer: COM0" if we set 'display=OpenThread Sniffer' without appending interface name
            print("interface {value=%s}{display=OpenThread Sniffer %s}" % (interface, interface))
        else:
            print("interface {value=%s}{display=OpenThread Sniffer}" % interface)
    stream.close()

def extcap_interfaces():
    """List available interfaces to capture from"""
    __console__ = sys.stdout
    DirtylogFile = open('dirtylog', 'w')
    sys.stderr = DirtylogFile
    print("extcap {version=0.0.0}{display=OpenThread Sniffer}{help=https://github.com/openthread/pyspinel}")

    for interface in comports():
        th = threading.Thread(target=serialopen, args=(interface, __console__, DirtylogFile))
        th.start()

def extcap_capture(interface, fifo, control_in, control_out, baudrate, channel, tap):
    """Start the sniffer to capture packets"""
    if sys.platform == 'win32':
        script = os.path.dirname(__file__) + '\sniffer.py'
    else:
        script = os.path.dirname(__file__) + '/sniffer.py'

    cmd = ['python', script, '-c', channel, '-u', interface, '--rssi', '-b', baudrate, '-o', str(fifo)]
    if tap:
        cmd.append('--tap')
    subprocess.Popen(cmd).wait()

def extcap_close_fifo(fifo):
    """"Close extcap fifo"""
    # This is apparently needed to workaround an issue on Windows/macOS
    # where the message cannot be read. (really?)
    fh = open(fifo, 'wb', 0)
    fh.close()


if __name__ == '__main__':

    # Capture options
    parser = argparse.ArgumentParser(description="OpenThread Sniffer extcap plugin")

    # Extcap Arguments
    parser.add_argument("--extcap-interfaces", help="Provide a list of interfaces to capture from", action="store_true")
    parser.add_argument("--extcap-interface", help="Provide the interface to capture from")
    parser.add_argument("--extcap-dlts", help="Provide a list of dlts for the given interface", action="store_true")
    parser.add_argument("--extcap-config", help="Provide a list of configurations for the given interface", action="store_true")
    parser.add_argument("--extcap-reload-option", help="Reload elements for the given option")
    parser.add_argument("--capture", help="Start the capture routine", action="store_true")
    parser.add_argument("--fifo", help="Use together with capture to provide the fifo to dump data to")
    parser.add_argument("--extcap-capture-filter", help="Used together with capture to provide a capture filter")
    parser.add_argument("--extcap-control-in", help="Used to get control messages from toolbar")
    parser.add_argument("--extcap-control-out", help="Used to send control messages to toolbar")

    # Interface Arguments
    parser.add_argument("--channel", help="IEEE 802.15.4 capture channel [11-26]")
    parser.add_argument("--baudrate", help="Serial port baud rate")
    parser.add_argument("--tap", help="IEEE 802.15.4 TAP (only for Wireshark3.0 and later)", action="store_true")

    try:
        args, unknown = parser.parse_known_args()
    except argparse.ArgumentError as exc:
        print("%s" % exc, file=sys.stderr)
        fifo_found = False
        fifo = ""
        for arg in sys.argv:
            if arg == "--fifo":
                fifo_found = True
            elif fifo_found:
                fifo = arg
                break
        extcap_close_fifo(fifo)
        parser.exit("ERROR_ARG")

    if len(unknown) > 1:
        print("Sniffer %d unknown arguments given:" % len(unknown))
        for unknown_item in unknown:
            print(unknown_item)

    if len(sys.argv) <= 1:
        parser.exit("No arguments given!")

    if not args.extcap_interfaces and args.extcap_interface is None:
        parser.exit("An interface must be provided or the selection must be displayed")

    if args.extcap_interfaces:
        extcap_interfaces()
        sys.exit(0)

    if args.extcap_config:
        extcap_config(args.extcap_interface, "")
    elif args.extcap_dlts:
        extcap_dlts(args.extcap_interface)
    elif args.capture:
        if args.fifo is None:
            parser.exit("The fifo must be provided to capture")
        try:
            extcap_capture(args.extcap_interface, args.fifo, args.extcap_control_in, args.extcap_control_out, args.baudrate, args.channel, args.tap)
        except KeyboardInterrupt:
            pass
        except:
            parser.exit("ERROR_INTERNAL")
    else:
        parser.print_help()
        parser.exit("ERROR_USAGE")
