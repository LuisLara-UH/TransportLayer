import socket
import logging

from socket_utils import create_receiver_socket, create_sender_socket
from utils import parse_address

class Conn:
    def __init__(self, sock):
        self.sock = sock


class ConnException(Exception):
    pass


def listen(address: str) -> Conn:
    sock = create_receiver_socket()

    host, port = parse_address(address)

    conn = Conn(sock)
    conn.sock.bind((host, port))
    conn.sock.listen(1)

    return conn


def accept(conn) -> Conn:
    pass


def dial(address) -> Conn:
    pass


def send(conn: Conn, data: bytes) -> int:
    pass


def recv(conn: Conn, length: int) -> bytes:
    pass


def close(conn: Conn):
    conn.sock.close()
    conn.sock = None
