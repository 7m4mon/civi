"""Bounded reassembly of IC-7300 USB scope packets (27 00).

Packet numbers are BCD. Never combine an incomplete sweep with a later sweep.
"""
import time
from .commands import unpack_bcd
from .errors import CiviError


def scope_frequency(data):
    # Scroll-mode lower edge can use F in the 1 GHz digit as a minus sign.
    if data[-1] >> 4 == 15:
        return -unpack_bcd(data[:-1]+bytes([data[-1] & 15]),True)
    return unpack_bcd(data,True)


class ScopeReceiver:
    def __init__(self):
        self.reset()
        self.latest = None
        self.invalid_packets = 0

    def reset(self):
        self.next_packet = 1
        self.points = []
        self.metadata = None

    def feed(self, data):
        try:
            if len(data) < 3 or data[0] != 0: raise ValueError()
            now, total = unpack_bcd(data[1:2]), unpack_bcd(data[2:3])
            if total != 11 or not 1 <= now <= total: raise ValueError()
            if now == 1:
                self.reset()
                if len(data) != 15 or data[3] > 3 or data[-1] not in (0,1): raise ValueError()
                self.metadata = {'mode':data[3], 'frequency_1_hz':scope_frequency(data[4:9]),
                                 'frequency_2_hz':scope_frequency(data[9:14]), 'out_of_range':bool(data[14])}
                if data[-1]:
                    self.latest = {**self.metadata,'points':[],'timestamp':time.time()}
                    self.reset(); return
                self.next_packet = 2
            else:
                if now != self.next_packet or self.metadata is None or any(p > 160 for p in data[3:]): raise ValueError()
                expected = 25 if now == 11 else 50
                if len(data)-3 != expected: raise ValueError()
                self.points.extend(data[3:])
                self.next_packet += 1
                if now == total:
                    if len(self.points) != 475: raise ValueError()
                    self.latest = {**self.metadata,'points':self.points.copy(),'timestamp':time.time()}
                    self.reset()
        except (ValueError,CiviError):
            self.invalid_packets += 1
            self.reset()

    def snapshot(self):
        latest = self.latest
        if latest is None or time.time()-latest['timestamp'] > 5: return None
        return {**latest,'points':latest['points'].copy()}
