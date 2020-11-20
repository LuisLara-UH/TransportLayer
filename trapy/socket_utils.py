import socket
from utils import parse_address
from pack_utils import create_syn_packet, create_from_receive
from timer import Timer
import time
import threading

mutex = threading.Lock()

SLEEP_INTERVAL = 0.05
TIMEOUT_INTERVAL = 0.5

sender_socket_protocol = socket.IPPROTO_RAW
receiver_socket_protocol = socket.IPPROTO_TCP

def create_sender_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, sender_socket_protocol)

    return sock

def create_receiver_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, receiver_socket_protocol)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    return sock

def wait_for_first_syn(sock):
    while True:
        pkt, _ = sock.recvfrom(1024)

        recv_pack = create_from_receive(pkt)
        if recv_pack.check_checksum() and recv_pack.is_syn:
            return recv_pack
        

def wait_for_synack(conn, pack):
    conn.sock.sendto(pack, (conn.dest_host, conn.dest_port))

    timer = Timer(TIMEOUT_INTERVAL) 
    threading.Thread(target=send_with_timer, args=(conn, pack, timer)).start()

    while True:
        pkt, _ = conn.sock.recvfrom(1024)
        
        recv_pack = create_from_receive(pkt)
        if recv_pack.check_checksum() and recv_pack.is_syn() and not recv_pack.is_ack() and recv_pack.ack == conn.seq_num and recv_pack.source_ip == conn.dest_host and recv_pack.source_port == conn.dest_port:
            mutex.acquire()
            timer.stop()
            mutex.release()

            return recv_pack


def wait_for_first_pack(conn, synack_pack):
    conn.sock.sendto(synack_pack, (conn.dest_host, conn.dest_port))

    timer = Timer(TIMEOUT_INTERVAL)
    threading.Thread(target=send_with_timer, args=(conn, synack_pack, timer)).start()

    while True:
        pkt, _ = conn.sock.recvfrom(1024)

        recv_pack = create_from_receive(pkt)
        if recv_pack.check_checksum() and not recv_pack.is_syn() and recv_pack.is_ack and recv_pack.seq_num == conn.seq_num and recv_pack.source_ip == conn.dest_host and recv_pack.source_port == conn.dest_port:
            mutex.acquire()
            timer.stop()
            mutex.release()

            return recv_pack

def send_with_timer(conn, pack, timer):
    timer.start()

    while True:
        mutex.acquire()
        if not timer.running():
            return
        if timer.timeout():
            timer.stop()
            conn.sock.sendto(pack, (conn.dest_host, conn.dest_port))
            timer.start()
        mutex.release()
        time.sleep(SLEEP_INTERVAL)