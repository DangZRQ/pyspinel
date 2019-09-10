#
#  Copyright (c) 2016-2017, The OpenThread Authors.
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
""" Module to provide codec utilities for .pcap formatters. """

import struct

PCAP_MAGIC_NUMBER = 0xa1b2c3d4
PCAP_VERSION_MAJOR = 2
PCAP_VERSION_MINOR = 4

DLT_IEEE802_15_4_WITHFCS = 195
DLT_IEEE802_15_4_TAP = 283
TLVS_LENGTH_DEFAULT = 12


FCS_TYPE = 0
FCS_LEN = 1
FCS_16bitCRC = 1
RSS_TYPE = 1
RSS_LEN = 4
LQI_TYPE = 10
LQI_LEN = 1
CHANNEL_TYPE = 3
CHANNEL_LEN = 3
CHANNEL_PAGE = 0


def crc( s ):
    # Some chips do not transmit the CRC, here we recalculate the CRC.

    crc = 0
    # remove the last 2 bytes
    for c in s[:-2]:
        c = ord(c)
        q = (crc ^ c) & 0x0f
        crc = (crc >> 4) ^ (q * 0x1081)
        q = (crc ^ (c >> 4)) & 0x0f
        crc = (crc >> 4) ^ (q * 0x1081)
    msb = chr( 0x0ff & (crc >> 8) )
    lsb = chr( 0x0ff & (crc >> 0) )
    s = s[:-2] + lsb + msb
    return s

class PcapCodec(object):
    """ Utility class for .pcap formatters. """

    @classmethod
    def encode_header(cls, dlt):
        """ Returns a pcap file header. """
        cls._dlt = dlt
        return struct.pack("<LHHLLLL",
                           PCAP_MAGIC_NUMBER,
                           PCAP_VERSION_MAJOR,
                           PCAP_VERSION_MINOR,
                           0, 0, 256,
                           cls._dlt)

    @classmethod
    def encode_frame(cls, frame, sec, usec, options_rssi, options_crc, metadata=None):
        """ Returns a pcap encapsulation of the given frame. """
        # write frame pcap header
        TLVs_length = TLVS_LENGTH_DEFAULT
        
        if options_crc:
            frame = crc(frame)
            TLVs_length += 8
            
        if options_rssi:
            if (cls._dlt == DLT_IEEE802_15_4_TAP):
                TLVs_length += 16
            else:
                # TI style FCS format: replace the last two bytes with RSSI and LQI
                frame = frame[:-2] + chr(metadata[0] & 0xff) + chr(metadata[3][1] & 0xff)
            
        if (cls._dlt == DLT_IEEE802_15_4_TAP):
            length = len(frame) + TLVs_length
        else:
            length = len(frame)

        pcap_frame = struct.pack("<LLLL", sec, usec, length, length)

        if (cls._dlt == DLT_IEEE802_15_4_TAP):
            # Append TLVs according to 802.15.4 TAP specification:
            # https://github.com/jkcko/ieee802.15.4-tap
            pcap_frame += struct.pack('<HH', 0, TLVs_length)
            pcap_frame += struct.pack('<HHHH', CHANNEL_TYPE, CHANNEL_LEN, metadata[3][0], CHANNEL_PAGE)
            if options_rssi:
                pcap_frame += struct.pack('<HHf', RSS_TYPE, RSS_LEN, metadata[0])
                pcap_frame += struct.pack('<HHI', LQI_TYPE, LQI_LEN, metadata[3][1])
            if options_crc:
                pcap_frame += struct.pack('<HHI', FCS_TYPE, FCS_LEN, FCS_16bitCRC)

        pcap_frame += frame
        return pcap_frame
