import socket
import random
from struct import pack, unpack

def create_packet(data : bytes, conn):
    flags = create_flag_field()
    return Packet(data, conn.localport, conn.dest_port, conn.dest_seq_num, conn.dest_seq_num, conn.localhost, conn.dest_host, flags)

def create_first_packet(data : bytes, conn):
    flags = create_flag_field(True)
    return Packet(data, conn.localport, conn.dest_port, conn.dest_seq_num, conn.dest_seq_num, conn.localhost, conn.dest_host, flags)

def create_syn_packet(conn):
    flag_field = create_flag_field(False, True)
    conn.seq_num = random.randint(100, 10000)

    packet = Packet(b'', conn.localport, conn.dest_port, conn.seq_num, 0, conn.localhost, conn.dest_host, flag_field)

    return packet.pack()

def create_synack_packet(conn):
    flag_field = create_flag_field(False, True)
    conn.seq_num = random.randint(100, 10000)

    packet = Packet(b'', conn.localport, conn.dest_port, conn.seq_num, conn.dest_seq_num, conn.localhost, conn.dest_host, flag_field)

    return packet.pack()

def create_from_receive(pack):
    new_pack = Packet()
    new_pack.unpack(pack)

    return new_pack

def create_flag_field(ack = False, syn = False, fin = False, cwr = False, ece = False):
    flag_field = 0

    if ack:
        flag_field += 0b00010000
    if syn:
        flag_field += 0b00000010
    if fin:
        flag_field += 0b00000001
    if cwr:
        flag_field += 0b10000000
    if ece:
        flag_field += 0b01000000

    return flag_field

def get_checksum(data : bytes):
    sum = 0
    for index in range(0,len(data),2):
        word = (data[index] << 8) + (data[index+1])
        sum = sum + word

    sum = (sum >> 16) + (sum & 0xffff)
    sum = ~sum & 0xffff

    return sum

class Packet:
    def __init__(self, data : bytes = b'',
                       source_port = 0, 
                       destination_port = 0,
                       sequence_number = 0,
                       ack = 0,
                       source_ip = '',
                       dest_ip = '',
                       flags = 0):
        self.source_port = source_port
        self.dest_port = destination_port
        self.seq_num = sequence_number
        self.ack = ack
        self.data_len = len(data)
        self.data = data
        self.checksum = 0
        self.source_ip = source_ip
        self.dest_ip = dest_ip
        self.flags = flags

    def pack(self):
        return self.ip_header_pack() + self.tcp_header_pack() + self.data

    def unpack(self, packed_data):
        ipHeader = packed_data[0:20]
        tcpHeader = packed_data[20:38]
        body = packed_data[38:]

        self.source_ip = socket.inet_ntoa(ipHeader[12:16])
        self.dest_ip = socket.inet_ntoa(ipHeader[16:20])
        self.source_port, self.dest_port, self.seq_num, self.ack, self.flags, _, self.data_len, self.checksum = unpack("!HHLLbbHH", tcpHeader)
        self.data = body

    def ip_header_pack(self):
        ip_header  = b'\x45\x00\x00\x28'  # Version, IHL, Type of Service | Total Length
        ip_header += b'\xab\xcd\x00\x00'  # Identification | Flags, Fragment Offset
        ip_header += b'\x40\x06\xa6\xec'  # TTL, Protocol | Header Checksum
        ip_header += socket.inet_aton(self.source_ip)  # Source Address
        ip_header += socket.inet_aton(self.dest_ip) # Destination Address

        return ip_header

    def tcp_header_pack(self):
        tcp_header  = pack('!HH', self.source_port, self.dest_port) # Source Port | Destination Port
        tcp_header += pack('!L', self.seq_num) # Sequence Number
        tcp_header += pack('!L', self.ack) # Acknowledgement Number
        tcp_header += pack('!bb', self.flags, 0) # Flags | Unused
        tcp_header += pack('!H', self.data_len) # Data Lenght

        self.checksum = get_checksum(tcp_header + self.data)
        tcp_header += pack('!H', self.checksum) # Checksum
        
        return tcp_header

    def check_checksum(self):
        tcp_header_without_ckecksum = pack('!HHLLbbH', self.source_port, self.dest_port, self.seq_num, self.ack, self.flags, 0, self.data_len)

        return (get_checksum(tcp_header_without_ckecksum + self.data) == self.checksum)

    def is_syn(self):
        is_syn = (self.flags >> 1) & 1

        return (is_syn == 1)

    def is_ack(self):
        is_ack = (self.flags >> 4) & 1

        return (is_ack == 1)