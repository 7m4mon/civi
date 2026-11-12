"""Windows UDP ancillary data for manually run, NIC-scoped LAN test fixtures.

Uses Microsoft WSARecvMsg/WSASendMsg and IN_PKTINFO. Never infer the incoming
interface from the client's source address (DHCP clients may use 0.0.0.0).
"""
import ctypes as C
import os
import select
import socket
import struct
import uuid


class Buffer(C.Structure):
    _fields_ = [('length', C.c_uint32), ('data', C.c_void_p)]


class Message(C.Structure):
    _fields_ = [('name', C.c_void_p), ('name_length', C.c_int),
                ('buffers', C.POINTER(Buffer)), ('count', C.c_uint32),
                ('control', Buffer), ('flags', C.c_uint32)]


class ControlHeader(C.Structure):
    _fields_ = [('length', C.c_size_t), ('level', C.c_int), ('kind', C.c_int)]


def align(size):
    boundary = C.sizeof(C.c_size_t)
    return (size + boundary - 1) & ~(boundary - 1)


class Datagram:
    def __init__(self, port=0, *, exclusive=True):
        if os.name != 'nt':
            raise OSError('Windows Winsock packet information is required')
        self.api = C.WinDLL('Ws2_32', use_last_error=True)
        self.api.WSAGetLastError.restype = C.c_int
        self.api.WSAIoctl.argtypes = [C.c_size_t, C.c_uint32, C.c_void_p, C.c_uint32,
                                     C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32), C.c_void_p, C.c_void_p]
        self.api.WSAIoctl.restype = C.c_int
        self.api.WSASendMsg.argtypes = [C.c_size_t, C.POINTER(Message), C.c_uint32,
                                       C.POINTER(C.c_uint32), C.c_void_p, C.c_void_p]
        self.api.WSASendMsg.restype = C.c_int
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET,
                                 socket.SO_EXCLUSIVEADDRUSE if exclusive else socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.setsockopt(socket.IPPROTO_IP, 19, 1)  # Windows IP_PKTINFO
            self.sock.bind(('0.0.0.0', port))
            self.sock.setblocking(False)
            guid = C.create_string_buffer(uuid.UUID('f689d7c8-6f1f-436b-8a53-e54fe351c322').bytes_le)
            pointer, count = C.c_void_p(), C.c_uint32()
            result = self.api.WSAIoctl(self.sock.fileno(), 0xC8000006, guid, 16,
                                       C.byref(pointer), C.sizeof(pointer), C.byref(count), None, None)
            self.check(result)
            prototype = C.WINFUNCTYPE(C.c_int, C.c_size_t, C.POINTER(Message),
                                      C.POINTER(C.c_uint32), C.c_void_p, C.c_void_p)
            self.receive_function = prototype(pointer.value)
        except BaseException:
            self.close()
            raise

    def check(self, result):
        if result == -1:
            code = self.api.WSAGetLastError()
            raise OSError(code, 'Winsock datagram operation failed')

    def receive(self, timeout=1):
        if not select.select([self.sock], [], [], timeout)[0]:
            return None
        payload, address, control = C.create_string_buffer(4096), C.create_string_buffer(16), C.create_string_buffer(256)
        buffer = Buffer(C.sizeof(payload), C.addressof(payload))
        message = Message(C.addressof(address), 16, C.pointer(buffer), 1,
                          Buffer(C.sizeof(control), C.addressof(control)), 0)
        count = C.c_uint32()
        self.check(self.receive_function(self.sock.fileno(), C.byref(message), C.byref(count), None, None))
        offset, interface, destination = 0, None, None
        while offset + C.sizeof(ControlHeader) <= message.control.length:
            header = ControlHeader.from_buffer_copy(control.raw, offset)
            start = offset + align(C.sizeof(ControlHeader))
            if header.length < start - offset or offset + header.length > message.control.length:
                raise OSError('Invalid ancillary-data length')
            if header.level == socket.IPPROTO_IP and header.kind == 19:
                if header.length != start - offset + 8:
                    raise OSError('Invalid Windows IN_PKTINFO')
                destination = socket.inet_ntoa(control.raw[start:start+4])
                interface = struct.unpack_from('=I', control.raw, start+4)[0]
            offset += align(header.length)
        if interface is None or message.name_length != 16:
            raise OSError('Missing packet interface information; refusing unscoped packet')
        family, port, ip, _ = struct.unpack('=HH4s8s', address.raw)
        if family != socket.AF_INET:
            raise OSError('Unexpected packet address family')
        return payload.raw[:count.value], (socket.inet_ntoa(ip), socket.ntohs(port)), interface, destination

    def send(self, payload, destination, interface, source):
        packet = C.create_string_buffer(payload)
        address = C.create_string_buffer(struct.pack('=HH4s8s', socket.AF_INET,
                                          socket.htons(destination[1]), socket.inet_aton(destination[0]), bytes(8)))
        buffer = Buffer(len(payload), C.addressof(packet))
        size = align(C.sizeof(ControlHeader)) + 8
        control = C.create_string_buffer(align(size))
        header = ControlHeader.from_buffer(control)
        header.length, header.level, header.kind = size, socket.IPPROTO_IP, 19
        data = socket.inet_aton(source) + struct.pack('=I', interface)
        C.memmove(C.addressof(control)+align(C.sizeof(ControlHeader)), data, 8)
        message = Message(C.addressof(address), 16, C.pointer(buffer), 1,
                          Buffer(C.sizeof(control), C.addressof(control)), 0)
        count = C.c_uint32()
        self.check(self.api.WSASendMsg(self.sock.fileno(), C.byref(message), 0, C.byref(count), None, None))
        if count.value != len(payload):
            raise OSError('Partial UDP packet send')

    def close(self):
        self.sock.close()
