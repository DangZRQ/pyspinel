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

# Nodeid is required to execute ot-ncp-ftd for its sim radio socket port.
# This is maximum that works for MacOS.
DEFAULT_NODEID = 34
COMMON_BAUDRATE = [460800, 115200, 9600]

ERROR_USAGE = 0
ERROR_ARG = 1
ERROR_INTERFACE = 2
ERROR_FIFO = 3
ERROR_INTERNAL = 4


def extcap_config(interface, option):
    """List configuration for the given interface"""
    args = []
    values = []
    args.append((0, '--channel', 'Channel', 'IEEE 802.15.4 channel', 'selector', '{required=true}{default=11}'))
    args.append((1, '--baudrate', 'Baudrate', 'Serial port baud rate', 'selector', '{required=true}{default=460800}'))

    if (len(option) <= 0):
        for arg in args:
            print("arg {number=%d}{call=%s}{display=%s}{tooltip=%s}{type=%s}%s" % arg)
        values = values + [(0, "%d" % i, "%d" % i, "true" if i == 11 else "false") for i in range(11, 27)]
        values = values + [(1, "%d" % b, "%d" % b, "true" if b == 460800 else "false") for b in COMMON_BAUDRATE]

    for value in values:
        print("value {arg=%d}{value=%s}{display=%s}{default=%s}" % value)

def extcap_dlts(interface):
    """List DLTs for the given interface"""
    print("dlt {number=195}{name=IEEE802_15_4_WITHFCS}{display=IEEE 802.15.4 with FCS}")

def serialopen(interface_port, STDOUT, DirtylogFile):
    sys.stdout = DirtylogFile
    stream = StreamOpen('u', str(interface_port).split()[0], False)
    wpan_api = WpanApi(stream, nodeid=DEFAULT_NODEID)
    value = wpan_api.prop_get_value(SPINEL.PROP_CAPS)

    if value is not None:
        sys.stdout = STDOUT
        if sys.platform == 'win32':
            print("interface {value=%s}{display=OpenThread Device %s}" % (str(interface_port).split()[0], str(interface_port).split()[0]))
        else:
            print("interface {value=%s}{display=OpenThread Device}" % str(interface_port).split()[0])
        sys.stdout = DirtylogFile
    stream.close()

def extcap_interfaces():
    """List available interfaces to capture from"""
    STDOUT = sys.stdout
    DirtylogFile = open('dirtylog', 'w')
    print("extcap {version=0.0.0}{display=OT Sniffer}{help=url}")

    for interface_port in comports():
        th = threading.Thread(target=serialopen, args=(interface_port, STDOUT, DirtylogFile))
        th.start()

def extcap_capture(interface, fifo, control_in, control_out, baudrate, channel):
    """Start the sniffer to capture packets"""
    script = os.path.dirname(__file__) + '\sniffer.py'
    cmd = ['python', script, '-c', channel, '-u', interface, '--crc', '--rssi', '-b', baudrate, '-o', str(fifo)]
    subprocess.Popen(cmd).wait()

def extcap_close_fifo(fifo):
    """"Close extcap fifo"""
    if not os.path.exists(fifo):
        print("FIFO does not exist!", file=sys.stderr)
        return

    # This is apparently needed to workaround an issue on Windows/macOS
    # where the message cannot be read. (really?)
    fh = open(fifo, 'wb', 0)
    fh.close()


if __name__ == '__main__':
    interface = ""
    option = ""

    # Capture options
    parser = argparse.ArgumentParser(description="Nordic Semiconductor nRF Sniffer extcap plugin")

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

    try:
        args, unknown = parser.parse_known_args()
    except argparse.ArgumentError as exc:
        print("%s" % exc, file=sys.stderr)
        fifo_found = False
        fifo = ""
        for arg in sys.argv:
            if arg == "--fifo" or arg == "--extcap-fifo":
                fifo_found = True
            elif fifo_found:
                fifo = arg
                break
        extcap_close_fifo(fifo)
        sys.exit(ERROR_ARG)

    if len(sys.argv) <= 1:
        parser.exit("No arguments given!")

    if not args.extcap_interfaces and args.extcap_interface is None:
        parser.exit("An interface must be provided or the selection must be displayed")

    if args.extcap_interfaces or args.extcap_interface is None:
        extcap_interfaces()
        sys.exit(0)

    if len(unknown) > 1:
        print("Sniffer %d unknown arguments given" % len(unknown))

    interface = args.extcap_interface

    if args.extcap_config:
        extcap_config(interface, option)
    elif args.extcap_dlts:
        extcap_dlts(interface)
    elif args.capture:
        if args.fifo is None:
            parser.print_help()
            sys.exit(ERROR_FIFO)
        channel = args.channel if args.channel else 11
        baudrate = args.baudrate if args.baudrate else 460800
        try:
            extcap_capture(interface, args.fifo, args.extcap_control_in, args.extcap_control_out, args.baudrate, args.channel)
        except KeyboardInterrupt:
            pass
        except:
            sys.exit(ERROR_INTERNAL)
    else:
        parser.print_help()
        sys.exit(ERROR_USAGE)
