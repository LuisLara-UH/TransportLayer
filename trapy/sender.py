from pack_utils import create_packet, create_from_receive, create_last
import time
import random
from timer import Timer
import threading

WINDOW_SIZE = 10
MAX_SEQ_NUM = 50000
MAX_SEND_TIMES = 10
PACKET_DATA_SIZE = 20
SLEEP_INTERVAL = 0.05
TIMEOUT_INTERVAL = 0.5

mutex = threading.Lock()

base = 0
send_timer = Timer(TIMEOUT_INTERVAL)
len_packets = 0
send_times = 0
received = { }
seq_num_to_index = { }

def send_data(conn, data : bytes):
    print('Sending...')
    global base, send_timer, mutex, len_packets, received, seq_num_to_index, send_times

    packets = divide_into_packets(conn, data)
    len_packets = len(packets)

    thread = threading.Thread(target=receive_ack, args=(conn,))
    thread.start()

    mutex.acquire()
    while base < len_packets:
        window_size = get_window_size(len(packets))
        for i in range(base, base + window_size):
            try:
                received[i]
            except KeyError:
                conn.sock.sendto(packets[i].pack(), (conn.dest_host, conn.dest_port))
                print('Packet', packets[i].seq_num, 'sent')

        send_timer.start()

        while send_timer.running() and not send_timer.timeout():
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()

        if send_timer.timeout():
            send_times += 1
            send_timer.stop()
        
        if send_times >= MAX_SEND_TIMES:
            break
    
    conn.seq_num = base
    mutex.release()
    if base == 0:
        return 0
    bytes_sent = packets[base - 1].data_len
    if base > 1:
        bytes_sent += (base - 1) * PACKET_DATA_SIZE
    return bytes_sent
    
def get_window_size(packet_length):
    global base, WINDOW_SIZE
    if packet_length == base + 1:
        return 1
    return min(WINDOW_SIZE, packet_length - base - 1)

def increase_window_size():
    global WINDOW_SIZE
    WINDOW_SIZE += 1

def decrease_window_size():
    global WINDOW_SIZE

    if WINDOW_SIZE > 1:
        WINDOW_SIZE /= 2

def divide_into_packets(conn, data : bytes):
    seq_num = conn.seq_num
    packets = []

    while len(data) > 0:
        seq_num_to_index[seq_num] = len(packets)

        if len(data) <= PACKET_DATA_SIZE:
            packets.append(create_last(data, conn, seq_num))
            break
        packets.append(create_packet(data[:PACKET_DATA_SIZE], conn, seq_num))
        seq_num += 1
        if seq_num == MAX_SEQ_NUM:
            seq_num = 0
        data = data[PACKET_DATA_SIZE:]

    return packets

def receive_ack(conn):
    global base, send_timer, mutex, len_packets, send_times

    while base < len_packets:
        pkt, _ = conn.sock.recvfrom(1024)

        recv_packet = create_from_receive(pkt)
        if recv_packet.source_ip == conn.dest_host and recv_packet.source_port == conn.dest_port and recv_packet.is_ack():
            mutex.acquire()
            index_ack = seq_num_to_index[recv_packet.ack]
            if index_ack >= base:
                print('Received ack:', recv_packet.ack)
                try:
                    received[index_ack]
                    received[index_ack] += 1
                except KeyError:
                    received[index_ack] = 1

                if received[index_ack] >= 3:
                    decrease_window_size()

                if index_ack == base:
                    send_timer.stop()
                    while True:
                        try:
                            received[base]
                            increase_window_size()
                            send_times = 0
                            base += 1
                        except KeyError:
                            break
            mutex.release()