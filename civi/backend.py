import json
import logging
import time
from .scope import ScopeReceiver
from pathlib import Path
from .errors import CiviError


def load_profile(name="ic7300"):
    if not name.replace("_", "").isalnum():
        raise ValueError("Invalid profile name")
    return json.loads((Path(__file__).parent / "profiles" / f"{name}.json").read_text())


def bcd_encode(value, count):
    if not 0 <= value < 10 ** (count * 2):
        raise ValueError("BCD out of range")
    return bytes(int(f"{value:0{count * 2}d}"[i:i+2], 16) for i in range(0, count * 2, 2))[::-1]


def bcd_decode(data, little=True):
    if any((b & 15) > 9 or (b >> 4) > 9 for b in data):
        raise CiviError(-310, "Invalid BCD response")
    return int("".join(f"{b:02x}" for b in (data[::-1] if little else data)))


class FrameParser:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, chunk):
        self.buffer.extend(chunk)
        frames = []
        while True:
            start = self.buffer.find(b"\xfe\xfe")
            if start < 0:
                self.buffer[:] = self.buffer[-1:] if self.buffer[-1:] == b"\xfe" else b""
                break
            del self.buffer[:start]
            # Additional FE preamble bytes are allowed.
            while self.buffer[:3] == b"\xfe\xfe\xfe":
                del self.buffer[0]
            end = self.buffer.find(b"\xfd", 2)
            if end < 0:
                if len(self.buffer) > 1024:
                    self.buffer.clear()
                break
            frame = bytes(self.buffer[:end + 1])
            del self.buffer[:end + 1]
            if len(frame) >= 6:
                frames.append(frame)
        return frames


class MockBackend:
    def __init__(self, profile):
        self.profile = profile
        self.state = "connected"
        self.frequency, self.mode, self.ptt = 7100000, "LSB", False
        self.failure = None
        self.command_values = {}
        self.scope_stream = False
        self.scope = ScopeReceiver()
        self.vfos = [{'frequency':7100000,'mode':0,'data':0,'filter':1},
                     {'frequency':14074000,'mode':1,'data':0,'filter':1}]
        self.selected_vfo = 0
        self.memory_mode = False
        self.memory_channel = 1
        self.memory_records = {}

    def _sync_display(self):
        if self.memory_mode:
            data = self.memory_records.get(self.memory_channel)
            if data and data != b'\xff':
                self.frequency = bcd_decode(data[1:6])
                self.mode = next(k for k,v in self.profile['modes'].items() if v == data[6])
        else:
            vfo = self.vfos[self.selected_vfo]
            self.frequency = vfo['frequency']
            self.mode = next(k for k,v in self.profile['modes'].items() if v == vfo['mode'])

    def _memory_record(self):
        mode = self.profile['modes'][self.mode]
        record = bcd_encode(self.frequency,5)+bytes([mode,1,0])+bytes.fromhex('000885000885')
        return b'\x00'+record*2+b' '*10

    def execute_command(self, spec, query, prefix, data):
        if self.failure:
            self.state = 'disconnected'
            raise CiviError(-365,self.failure)
        self.state = 'connected'
        key = prefix.hex()
        key = {'1a050081':'1419','1a07':'1665'}.get(key,key)
        header = spec.header
        if query:
            if header in ('RAD:VFO:FREQ','RAD:VFO:MODE'):
                vfo = self.vfos[self.selected_vfo ^ prefix[-1]]
                encoded = bcd_encode(vfo['frequency'],5) if header.endswith('FREQ') else bytes([vfo['mode'],vfo['data'],vfo['filter']])
            elif header == 'RAD:MEM:CONTENT':
                channel = bcd_decode(prefix[-2:],little=False)
                encoded = self.memory_records.get(channel,b'\xff')
            else:
                encoded = self.command_values.get(key, spec.codec.encode(spec.codec.sample()))
            if spec.codec.kind == 'tone': encoded = b'\x00'+encoded
            return spec.codec.decode(encoded)
        self.command_values[key] = data
        if header in ('RAD:VFO:FREQ','RAD:VFO:MODE'):
            vfo = self.vfos[self.selected_vfo ^ prefix[-1]]
            if header.endswith('FREQ'): vfo['frequency'] = bcd_decode(data)
            else: vfo.update(zip(('mode','data','filter'),data))
            self._sync_display()
        elif header == 'RAD:VFO:SELECT':
            self.selected_vfo = data[0]
            self.memory_mode = False
            self._sync_display()
        elif header == 'RAD:VFO:ENABLE':
            self.memory_mode = False; self._sync_display()
        elif header == 'RAD:VFO:COPY':
            self.vfos[self.selected_vfo ^ 1] = self.vfos[self.selected_vfo].copy()
        elif header == 'RAD:VFO:SWAP':
            self.vfos.reverse(); self._sync_display()
        elif header == 'RAD:MEM:CONTENT':
            self.memory_records[bcd_decode(prefix[-2:],little=False)] = data
            self._sync_display()
        elif header == 'RAD:MEM:SELECT':
            self.memory_channel = bcd_decode(data,little=False)
            self.memory_mode = True; self._sync_display()
        elif header == 'RAD:MEM:ENABLE':
            self.memory_mode = True; self._sync_display()
        elif header == 'RAD:MEM:WRITE':
            self.memory_records[self.memory_channel] = self._memory_record()
        elif header == 'RAD:MEM:CLEAR':
            self.memory_records[self.memory_channel] = b'\xff'
        elif header == 'RAD:MEM:TOVFO':
            rec = self.memory_records.get(self.memory_channel)
            if rec and rec != b'\xff':
                self.vfos[self.selected_vfo].update(frequency=bcd_decode(rec[1:6]),mode=rec[6],filter=rec[7],data=rec[8]>>4)
        if spec.header in ('RAD:CW:SEND','RAD:VOICE'):
            self.ptt = spec.header == 'RAD:CW:SEND' or data != b'\x00'
        if spec.header == 'RAD:CW:STOP': self.ptt = False
        if spec.header == 'RAD:SCOPE:STREAM':
            self.scope_stream = data == b'\x01'
            self.scope.reset(); self.scope.latest = None
        return None

    def poll_events(self):
        if self.scope_stream:
            self.scope.latest = {'mode':0,'frequency_1_hz':self.frequency,'frequency_2_hz':50000,
                                 'out_of_range':False,'points':[40 + i % 80 for i in range(475)],'timestamp':time.time()}

    def call(self, op, value=None):
        if self.failure:
            self.state = "disconnected"
            raise CiviError(-365, self.failure)
        self.state = "connected"
        if op == "model_id_get": return self.profile["model_id"]
        if op == "frequency_get": return self.frequency
        if op == "mode_get": return self.mode
        if op == "smeter_get": return 96
        if op == "ptt_get": return self.ptt
        if op == "frequency_set":
            self.frequency = value
            if not self.memory_mode: self.vfos[self.selected_vfo]['frequency'] = value
        elif op == "mode_set":
            self.mode = value
            if not self.memory_mode: self.vfos[self.selected_vfo].update(mode=self.profile['modes'][value],filter=1)
        elif op == "ptt_set": self.ptt = value

    def recover(self):
        self.failure = None
        self.state = "connected"
        self.scope_stream = False
        self.scope.latest = None

    def close(self):
        self.state = "disconnected"
        self.scope_stream = False
        self.scope.latest = None


class CivBackend:
    """Only the service worker calls this synchronous serial owner.

    CI-V has no transaction IDs. After uncertain I/O, all operations except
    best-effort PTT OFF are quarantined until an operator resets the radio/link.
    """
    def __init__(self, profile, settings, factory=None):
        self.profile, self.settings = profile, settings.copy()
        self.factory, self.port = factory, None
        self._open_error = None
        self.trace_sink = None
        self._scope_trace_time = None
        self._scope_trace_count = 0
        self.parser = FrameParser()
        self.state = "disconnected"
        self.notifications = []
        self.scope_stream = False
        self.scope = ScopeReceiver()

    def _trace(self, direction, data):
        if not self.settings.get('trace_frames', True): return
        detail = ''
        if direction == 'RX' and data[4:6] == b'\x27\x00' and not self.settings.get('trace_scope_frames', False):
            self._scope_trace_count += 1
            now = time.monotonic()
            if self._scope_trace_time is not None and now - self._scope_trace_time < 2: return
            detail = f' [scope sample; {self._scope_trace_count} packet(s) since previous sample]'
            self._scope_trace_time = now
            self._scope_trace_count = 0
        message = f'CI-V {direction}{detail}: {data.hex(" ").upper()}'
        logging.getLogger('civi.wire').info(message)
        if self.trace_sink is not None: self.trace_sink(message)

    def _event(self, frame):
        radio, controller = self.settings['radio_address'],self.settings['controller_address']
        if frame[3] != radio or frame[2] not in (0,controller): return False
        payload = frame[4:-1]
        if payload[:2] == b'\x27\x00':
            if self.scope_stream: self.scope.feed(payload[2:])
            return True
        if frame[2] == 0 and payload[:1] in (b'\x00',b'\x01'):
            self.notifications.append(payload.hex())
            self.notifications[:] = self.notifications[-32:]
            return True
        return False

    def poll_events(self):
        if not self.port or not self.scope_stream: return
        try:
            remaining = 16384
            while remaining > 0 and (count := getattr(self.port,'in_waiting',0)):
                chunk = self.port.read(min(count,remaining))
                if not chunk: break
                remaining -= len(chunk)
                for frame in self.parser.feed(chunk):
                    self._trace('RX', frame)
                    self._event(frame)
        except Exception as e:
            self.state = 'quarantined'
            self.scope.latest = None
            raise CiviError(-365,'USB scope read failed; link quarantined') from e

    def execute_command(self, spec, query, prefix, data):
        if not query and spec.header == 'RAD:SCOPE:STREAM' and data == b'\x01':
            if self.settings['baud'] != 115200: raise CiviError(-221,'IC-7300 scope requires 115200 baud')
            if self._exchange(bytes.fromhex('1a050074')) != b'\x01':
                raise CiviError(-221,'Scope requires CI-V USB port unlinked from REMOTE')
        preamble = 0
        if not query and spec.header == 'RAD:POWER:ON':
            baud = self.settings['baud']
            preamble = {115200:150,57600:75,38400:50,19200:25,9600:13,4800:7}.get(baud, max(7,int(baud/768)))
        stop = not query and (spec.header in ('RAD:CW:STOP','RAD:POWER:ON','RAD:POWER:OFF') or spec.header in ('RAD:VOICE','RAD:VOX','RAD:BKIN','RAD:TUNER','RAD:SCOPE:STREAM') and data == b'\x00')
        uncertain_stop = stop and self.state == 'quarantined'
        response = self._exchange(prefix+data,ack=not query,preamble=preamble,emergency=stop)
        if uncertain_stop: raise CiviError(-365,'Recovery/stop action attempted; quarantined ACK cannot confirm completion')
        if not query:
            if spec.header == 'RAD:SCOPE:STREAM':
                self.scope_stream = data == b'\x01'
                self.scope.reset(); self.scope.latest = None
            return None
        try: return spec.codec.decode(response)
        except (CiviError,ValueError,UnicodeError) as e:
            self.state = 'quarantined'
            raise CiviError(-310,'Malformed extended CI-V response') from e

    def _open(self):
        if self.port is None:
            logger = logging.getLogger('civi.serial')
            if self._open_error is None:
                logger.info('Opening serial port %s at %s baud (radio 0x%02X, controller 0x%02X)',
                            self.settings['port'], self.settings['baud'],
                            self.settings['radio_address'], self.settings['controller_address'])
            try:
                if self.factory is None:
                    import serial
                    s = serial.Serial()
                    s.port = self.settings["port"]
                    s.baudrate = self.settings["baud"]
                    s.timeout = 0.05
                    s.write_timeout = self.settings["timeout"]
                    # Do not key USB SEND/RTS/DTR on opening the serial port.
                    s.dtr = s.rts = False
                    s.open()
                    self.port = s
                else:
                    self.port = self.factory()
                self.parser = FrameParser()
                self._open_error = None
                logger.info('Serial port %s opened successfully; waiting for a CI-V response', self.settings['port'])
            except Exception as e:
                self.state = "disconnected"
                error = (self.settings['port'], self.settings['baud'], type(e).__name__, str(e))
                if error != self._open_error:
                    logger.warning('Cannot open serial port %s at %s baud: %s: %s. Retrying in the background; Web remains available.',
                                   self.settings['port'], self.settings['baud'], type(e).__name__, e)
                    self._open_error = error
                raise CiviError(-365, "USB serial unavailable") from e

    def _exchange(self, command, ack=False, emergency=False, preamble=0):
        if self.state == "quarantined" and not emergency:
            raise CiviError(-365, "Link quarantined; reset radio/link and recover explicitly")
        self._open()
        radio = self.settings["radio_address"]
        controller = self.settings["controller_address"]
        request = b"\xfe\xfe" + bytes([radio, controller]) + command + b"\xfd"
        try:
            # Flush frames received before this operation, never treat them as replies.
            if self.scope_stream:
                self.poll_events()
            else:
                self.port.reset_input_buffer()
                self.parser = FrameParser()
            if preamble:
                wake = b'\xfe'*preamble
                if self.port.write(wake) != len(wake): raise OSError('Short wake preamble write')
                self._trace('TX wake preamble', wake)
            if self.port.write(request) != len(request):
                raise OSError("Short serial write")
            self._trace('TX', request)
            deadline = time.monotonic() + self.settings["timeout"]
            while time.monotonic() < deadline:
                frames = self.parser.feed(self.port.read(256))
                for frame in frames: self._trace('RX', frame)
                for frame in frames:
                    if frame == request: continue
                    if self._event(frame): continue
                    dest, source, payload = frame[2], frame[3], frame[4:-1]
                    if source != radio or dest != controller: continue
                    if payload == b"\xfa":
                        self.state = "connected" if not emergency else self.state
                        raise CiviError(-200, f"Radio rejected CI-V {command.hex(' ').upper()} (NAK)")
                    if ack and payload == b"\xfb":
                        if not emergency: self.state = "connected"
                        return b""
                    if not ack and payload.startswith(command) and len(payload) > len(command):
                        if not emergency: self.state = "connected"
                        return payload[len(command):]
            raise CiviError(-365, "CI-V response timeout; link quarantined")
        except CiviError as e:
            if e.code == -365: self.state = "quarantined"
            raise
        except Exception as e:
            self.state = "quarantined"
            self._close_port()
            raise CiviError(-365, "USB I/O failed; link quarantined") from e

    def call(self, op, value=None):
        if op not in self.profile["commands"]:
            raise CiviError(-241, "Unsupported radio feature")
        cmd = bytes.fromhex(self.profile["commands"][op])
        if op == "frequency_set": cmd += bcd_encode(value, 5)
        if op == "mode_set": cmd += bytes([self.profile["modes"][value]])
        if op == "ptt_set": cmd += bytes([int(value)])
        uncertain_stop = self.state == "quarantined" and op == "ptt_set" and value is False
        data = self._exchange(cmd, ack=op.endswith("set"), emergency=op == "ptt_set" and value is False)
        if uncertain_stop:
            raise CiviError(-365, "PTT OFF attempted; quarantined ACK cannot confirm stop")
        try:
            if op == "model_id_get":
                if len(data) != 1: raise ValueError()
                return data[0]
            if op == "frequency_get":
                if len(data) != 5: raise ValueError()
                result = bcd_decode(data)
                if not any(lo <= result <= hi for lo, hi in self.profile["frequency_ranges"]): raise ValueError()
                return result
            if op == "mode_get":
                if len(data) != 2 or data[1] not in (1, 2, 3): raise ValueError()
                return next(k for k, v in self.profile["modes"].items() if v == data[0])
            if op == "smeter_get":
                if len(data) != 2: raise ValueError()
                value = bcd_decode(data, little=False)
                if not 0 <= value <= 255: raise ValueError()
                return value
            if op == "ptt_get":
                if len(data) != 1 or data[0] not in (0, 1): raise ValueError()
                return bool(data[0])
        except (ValueError, StopIteration, CiviError) as e:
            self.state = "quarantined"
            raise CiviError(-310, "Malformed or unsupported CI-V response") from e

    def _close_port(self):
        if self.port:
            try: self.port.close()
            finally: self.port = None

    def recover(self):
        self._close_port()
        self.scope_stream = False
        self.scope.latest = None
        self.state = "disconnected"
        self._open()
        self.call("frequency_get")

    def close(self):
        self._close_port()
        self.state = "disconnected"
        self.scope_stream = False
        self.scope.latest = None
