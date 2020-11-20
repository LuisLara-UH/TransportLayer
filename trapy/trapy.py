import socket
import logging

from socket_utils import *
from utils import parse_address
from pack_utils import create_syn_packet, create_from_receive, create_first_packet, create_synack_packet
from struct import pack, unpack
from timer import Timer
from sender import send_data
from receiver import receive

IP_ADDRESS_CLIENT = '10.0.0.1'
PORT_CLIENT = 8080
IP_ADDRESS_SERVER = '10.0.0.2'
PORT_SERVER = 8080


class Conn:
    def __init__(self, localhost, localport):
        self.sock = create_receiver_socket()
        self.localhost = localhost
        self.localport = localport
        self.sock.bind((localhost, localport))

class ConnException(Exception):
    pass


def listen(address: str) -> Conn:
    host, port = parse_address(address)

    conn = Conn(host, port)

    print('Listening...')

    return conn


def accept(conn) -> Conn:
    print('Waiting for SYN...')
    pack = wait_for_first_syn(conn.sock)
    print('SYN received')

    conn.dest_host = pack.source_ip
    conn.dest_port = pack.source_port
    conn.dest_seq_num = pack.seq_num

    synack_pack = create_synack_packet(conn)
    print('Sending SYNACK. Waiting for first pack...')
    wait_for_first_pack(conn, synack_pack)
    print('First pack received')

    return conn

def dial(address : str) -> Conn:
    print('Dialing...')

    host, port = parse_address(address)
    conn = Conn(IP_ADDRESS_CLIENT, PORT_CLIENT)

    conn.dest_host = host
    conn.dest_port = port
    
    syn_pack = create_syn_packet(conn)
    print('Waiting for SYNACK...')
    pack = wait_for_synack(conn, syn_pack)
    print('SYNACK received')
    
    conn.dest_seq_num = pack.seq_num

    first_pack = create_first_packet(b'', conn)
    conn.sock.sendto(first_pack.pack(), (conn.dest_host, conn.dest_port))

    return conn


def send(conn: Conn, data: bytes) -> int:
    send_data(conn, data)


def recv(conn: Conn, length: int) -> bytes:
    packets = receive(conn, length)
    data = b''

    for packet in packets:
        data += packet.data[:packet.data_len]

    return data


def close(conn: Conn):
    conn.sock.close()
    conn.sock = None