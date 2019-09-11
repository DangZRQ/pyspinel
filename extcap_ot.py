#!/usr/bin/env python3
#
#  Copyright (c) 2019, The OpenThread Authors.
#  All rights reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
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

class Config(Enum):
    CHANNEL = 0
    BAUDRATE = 1
    TAP = 2

def extcap_config(interface, option):
    """List Configuration for the given interface"""
    args = []
    values = []
    args.append((Config.CHANNEL.value, '--channel', 'Channel', 'IEEE 802.15.4 channel', 'selector', '{required=true}{default=11}'))
    args.append((Config.TAP.value, '--tap', 'IEEE 802.15.4 TAP (only for Wireshark3.0 and later)', 'IEEE 802.15.4 TAP', 'boolflag', '{default=yes}'))

    for arg in args:
        print('arg {number=%d}{call=%s}{display=%s}{tooltip=%s}{type=%s}%s' % arg)

    values = values + [(Config.CHANNEL.value, '%d' % i, '%d' % i, 'true' if i == 11 else 'false') for i in range(11, 27)]

    for value in values:
        print('value {arg=%d}{value=%s}{display=%s}{default=%s}' % value)

def extcap_dlts(interface):
    """List DLTs for the given interface"""
    print('dlt {number=195}{name=IEEE802_15_4_WITHFCS}{display=IEEE 802.15.4 with FCS}')
    print('dlt {number=283}{name=IEEE802_15_4_TAP}{display=IEEE 802.15.4 TAP}')

def serialopen(interface,  __console__, DirtylogFile):
    """
    Open serial to indentify OpenThread sniffer
    :param interface: string, eg: '/dev/ttyUSB0 - Zolertia Firefly platform', '/dev/ttyACM1 - nRF52840 OpenThread Device'
    """
    sys.stdout = DirtylogFile
    sys.stderr = DirtylogFile
    interface = str(interface).split()[0]

    stream = StreamOpen('u', interface, False)
    wpan_api = WpanApi(stream, nodeid=DEFAULT_NODEID)
    value = wpan_api.prop_get_value(SPINEL.PROP_CAPS)

    sys.stdout = __console__
    sys.stderr = __console__

    if value is not None:
        if sys.platform == 'win32':
            # Wireshark only shows the value of key `display`('OpenThread Sniffer').
            # Here intentionally appends interface in the end (e.g. 'OpenThread Sniffer: COM0').
            print('interface {value=%s}{display=OpenThread Sniffer %s}' % (interface, interface))
        else:
            # On Linux or MacOS, wireshark will show the concatenation of the content of `display`
            # and `interface` by default (e.g. 'OpenThread Sniffer: /dev/ttyACM0').
            print('interface {value=%s}{display=OpenThread Sniffer}' % interface)
    stream.close()

def detect_baudrate(interface):
    right_baudrate = None

    for speed in COMMON_BAUDRATE:
        stream = StreamOpen('u', interface, False, baudrate=speed)
        wpan_api = WpanApi(stream, nodeid=DEFAULT_NODEID)
        result = wpan_api.prop_set_value(SPINEL.PROP_PHY_ENABLED, 1)
        if not result:
            stream.close()
            continue
        else:
            right_baudrate = speed
            break

    stream.close()
    return right_baudrate

def extcap_baudrate(interface):
    baudrate = detect_baudrate(interface)
    if baudrate is not None:
        print('baudrate:%s' % baudrate)

def extcap_interfaces():
    """List available interfaces to capture from"""
    __console__ = sys.stdout
    DirtylogFile = open('dirtylog', 'w')
    print('extcap {version=0.0.0}{display=OpenThread Sniffer}{help=https://github.com/openthread/pyspinel}')

    for interface in comports():
        th = threading.Thread(target=serialopen, args=(interface, __console__, DirtylogFile))
        th.start()

def extcap_capture(interface, fifo, control_in, control_out, channel, tap):
    """Start the sniffer to capture packets"""
    baudrate = detect_baudrate(interface)

    if baudrate is not None:
        cmd = ['python', 'sniffer.py', '-c', channel, '-u', interface, '--rssi', '-b', str(baudrate), '-o', str(fifo)]
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
    parser = argparse.ArgumentParser(description='OpenThread Sniffer extcap plugin')

    # Extcap Arguments
    parser.add_argument('--extcap-interfaces', help='Provide a list of interfaces to capture from', action='store_true')
    parser.add_argument('--extcap-interface', help='Provide the interface to capture from')
    parser.add_argument('--extcap-dlts', help='Provide a list of dlts for the given interface', action='store_true')
    parser.add_argument('--extcap-config', help='Provide a list of configurations for the given interface', action='store_true')
    parser.add_argument('--extcap-reload-option', help='Reload elements for the given option')
    parser.add_argument('--capture', help='Start the capture routine', action='store_true')
    parser.add_argument('--fifo', help='Use together with capture to provide the fifo to dump data to')
    parser.add_argument('--extcap-capture-filter', help='Used together with capture to provide a capture filter')
    parser.add_argument('--extcap-control-in', help='Used to get control messages from toolbar')
    parser.add_argument('--extcap-control-out', help='Used to send control messages to toolbar')
    parser.add_argument('--extcap-baudrate', help='Auto detect the baudrate of the given interface', action='store_true')

    # Interface Arguments
    parser.add_argument('--channel', help='IEEE 802.15.4 capture channel [11-26]')
    parser.add_argument('--tap', help='IEEE 802.15.4 TAP (only for Wireshark3.0 and later)', action='store_true')

    try:
        args, unknown = parser.parse_known_args()
    except argparse.ArgumentError as exc:
        print('%s' % exc, file=sys.stderr)
        fifo_found = False
        fifo = ''
        for arg in sys.argv:
            if arg == '--fifo':
                fifo_found = True
            elif fifo_found:
                fifo = arg
                break
        extcap_close_fifo(fifo)
        parser.exit('ERROR_ARG')

    if len(unknown) > 0:
        parser.exit('Sniffer %d unknown arguments given: %s' % (len(unknown), unknown))

    if len(sys.argv) == 0:
        parser.print_help()
        parser.exit('No arguments given!')

    if not args.extcap_interfaces and args.extcap_interface is None:
        parser.exit('An interface must be provided or the selection must be displayed')

    if args.extcap_interfaces:
        extcap_interfaces()
        sys.exit(0)

    if args.extcap_config:
        extcap_config(args.extcap_interface, '')
    elif args.extcap_dlts:
        extcap_dlts(args.extcap_interface)
    elif args.extcap_baudrate:
        extcap_baudrate(args.extcap_interface)
    elif args.capture:
        if args.fifo is None:
            parser.exit('The fifo must be provided to capture')
        try:
            extcap_capture(args.extcap_interface, args.fifo, args.extcap_control_in, args.extcap_control_out, args.channel, args.tap)
        except KeyboardInterrupt:
            pass
        except:
            parser.exit('ERROR_INTERNAL')
    else:
        parser.print_help()
        parser.exit('ERROR_USAGE')