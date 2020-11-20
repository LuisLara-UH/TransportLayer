#from trapy import *
from pack_utils import create_packet, create_from_receive
import time
from timer import Timer
import threading

WINDOW_SIZE = 10
SLEEP_INTERVAL = 0.05
TIMEOUT_INTERVAL = 0.5

mutex = threading.Lock()

base = 0
send_timer = Timer(TIMEOUT_INTERVAL)

def send_data(conn, data : bytes):
    global base, send_timer, mutex

    packets = divide_into_packets(conn, data)

    threading.Thread(target=receive_ack, args=(conn,)).start()

    mutex.acquire()
    while base < len(packets):
        window_size = get_window_size(len(packets))
        for i in range(base, base + window_size):
            conn.sock.sendto(packets[i].pack(), (conn.dest_host, conn.dest_port))

        send_timer.start()

        while send_timer.running() and not send_timer.timeout():
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()

        if send_timer.timeout():
            send_timer.stop()
        else:
            window_size = get_window_size(len(packets))
    
def get_window_size(packet_length):
    global base
    return min(WINDOW_SIZE, packet_length - base)

def divide_into_packets(conn, data : bytes):
    seq_num = conn.seq_num
    packets = []

    while len(data) > 0:
        if len(data) < 20:
            packets.append(create_packet(data, conn, seq_num))
            break
        packets.append(create_packet(data[:20], conn, seq_num))
        seq_num += 1
        data = data[20:]

    return packets

def receive_ack(conn):
    global base, send_timer, mutex

    while True:
        pkt, _ = conn.sock.recvfrom(1024)

        recv_packet = create_from_receive(pkt)
        if recv_packet.source_ip == conn.dest_host and recv_packet.source_port == conn.dest_port and recv_packet.is_ack():
            mutex.acquire()
            if recv_packet.seq_num > base:
                base = recv_packet.seq_num + 1
                send_timer.stop()
            mutex.release()