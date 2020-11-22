from pack_utils import create_from_receive, create_ack, create_fin_packet
import random
from timer import Timer
import threading
import time

SLEEP_INTERVAL = 0.05
TIMEOUT_INTERVAL = 10

mutex = threading.Lock()

new_packet = None
recv_timer = Timer(TIMEOUT_INTERVAL)

def receive(conn, length):
    global new_packet, recv_timer
    print('Receiving...')
    seq_num = conn.dest_seq_num
    packets = []
    received = { }

    while seq_num < conn.dest_seq_num + length:
        recv_timer.start()
        thread = threading.Thread(target=receive_packet, args=(conn,))
        thread.start()

        mutex.acquire()
        while recv_timer.running() and not recv_timer.timeout():
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()

        if recv_timer.timeout():
            print('Receive timeout')
            mutex.release()
            break
        recv_timer.stop()
        
        if new_packet.is_fin():
            fin_pack = create_fin_packet(conn)
            conn.sock.sendto(fin_pack.pack(), (conn.dest_host, conn.dest_port))
            conn.close = True
            break

        if new_packet.source_ip == conn.dest_host and new_packet.source_port == conn.dest_port:
            if new_packet.seq_num < conn.dest_seq_num or new_packet.seq_num > conn.dest_seq_num + length:
                continue
            if new_packet.seq_num > seq_num or new_packet.seq_num == seq_num:
                print('Received', new_packet.seq_num)
                received[new_packet.seq_num] = new_packet
            print('Sending ack', new_packet.seq_num)
            ack = create_ack(conn, new_packet.seq_num)
            conn.sock.sendto(ack.pack(), (conn.dest_host, conn.dest_port))

            while True:
                try:
                    received[seq_num]
                    seq_num += 1
                except:
                    break

            try:
                if received[seq_num - 1].is_last():
                    ack = create_ack(conn, received[seq_num - 1].seq_num)
                    conn.sock.sendto(ack.pack(), (conn.dest_host, conn.dest_port))
                    break
            except:
                pass
        mutex.release()

    for i in range(conn.dest_seq_num, seq_num):
        packets.append(received[i])
    conn.dest_seq_num = seq_num

    return packets

def receive_packet(conn):
    global new_packet, recv_timer
    pkt, _ = conn.sock.recvfrom(1024)

    mutex.acquire()
    new_packet = create_from_receive(pkt)
    recv_timer.stop()
    mutex.release()