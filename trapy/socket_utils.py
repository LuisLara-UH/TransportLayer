import socket
from utils import parse_address
from pack_utils import create_syn_packet, create_from_receive
from timer import Timer
import time
import threading

mutex = threading.Lock()

SLEEP_INTERVAL = 0.05
TIMEOUT_INTERVAL = 0.5

recv_pack = None

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
    global recv_pack
    conn.sock.sendto(pack, (conn.dest_host, conn.dest_port))

    timer = Timer(TIMEOUT_INTERVAL) 
    threading.Thread(target=receive_synack, args=(conn, timer)).start()
    timer.start()

    while True:
        mutex.acquire()
        if not timer.running():
            mutex.release()
            return recv_pack
        if timer.timeout():
            timer.stop()
            conn.sock.sendto(pack, (conn.dest_host, conn.dest_port))
            timer.start()
        mutex.release()
        time.sleep(SLEEP_INTERVAL)

def receive_synack(conn, timer):
    global recv_pack
    while True:
        pkt, _ = conn.sock.recvfrom(1024)
        
        mutex.acquire()
        recv_pack = create_from_receive(pkt)
        if recv_pack.check_checksum() and recv_pack.is_syn() and not recv_pack.is_ack() and recv_pack.ack == conn.seq_num and recv_pack.source_ip == conn.dest_host and recv_pack.source_port == conn.dest_port:
            timer.stop()
            mutex.release()
            break
        mutex.release()


def wait_for_first_pack(conn, synack_pack):
    global recv_pack
    conn.sock.sendto(synack_pack, (conn.dest_host, conn.dest_port))

    timer = Timer(TIMEOUT_INTERVAL)
    threading.Thread(target=receive_first_pack, args=(conn, timer)).start()
    timer.start()

    send_times = 1

    while True:
        mutex.acquire()
        if not timer.running():
            mutex.release()
            return recv_pack
        if timer.timeout():
            timer.stop()
            conn.sock.sendto(synack_pack, (conn.dest_host, conn.dest_port))
            send_times += 1
            if send_times >= 5:
                mutex.release()
                break
            timer.start()
        mutex.release()
        time.sleep(SLEEP_INTERVAL)


def receive_first_pack(conn, timer):
    global recv_pack
    while True:
        pkt, _ = conn.sock.recvfrom(1024)

        mutex.acquire()
        recv_pack = create_from_receive(pkt)
        if recv_pack.check_checksum() and not recv_pack.is_syn() and recv_pack.is_ack() and recv_pack.seq_num == conn.seq_num and recv_pack.source_ip == conn.dest_host and recv_pack.source_port == conn.dest_port:
            timer.stop()
            mutex.release()
            break
        mutex.release()

def wait_for_fin(conn, fin_pack):
    global recv_pack
    conn.sock.sendto(fin_pack, (conn.dest_host, conn.dest_port))

    timer = Timer(TIMEOUT_INTERVAL)
    threading.Thread(target=receive_fin, args=(conn, timer)).start()
    timer.start()

    send_times = 1

    while True:
        mutex.acquire()
        if not timer.running():
            mutex.release()
            break
        if timer.timeout():
            timer.stop()
            conn.sock.sendto(fin_pack, (conn.dest_host, conn.dest_port))
            send_times += 1
            if send_times >= 5:
                mutex.release()
                break
            timer.start()
        mutex.release()
        time.sleep(SLEEP_INTERVAL)


def receive_fin(conn, timer):
    global recv_pack
    while True:
        pkt, _ = conn.sock.recvfrom(1024)

        mutex.acquire()
        recv_pack = create_from_receive(pkt)
        if recv_pack.check_checksum() and recv_pack.is_fin() and recv_pack.source_ip == conn.dest_host and recv_pack.source_port == conn.dest_port:
            timer.stop()
            mutex.release()
            break
        mutex.release()