from pack_utils import create_from_receive, create_ack

def receive(conn, length):
    seq_num = conn.dest_seq_num
    packets = []
    received = { }

    while seq_num < conn.dest_seq_num + length:
        pkt, _ = conn.sock.recvfrom(1024)

        new_packet = create_from_receive(pkt)
        if new_packet.is_ack():
            if new_packet.seq_num < conn.dest_seq_num or new_packet.seq_num > conn.dest_seq_num + length:
                continue
            if new_packet.seq_num < seq_num or new_packet.seq_num == seq_num:
                ack = create_ack(conn, new_packet.seq_num)
                conn.sock.sendto(ack, (conn.dest_host, conn.dest_port))
            if new_packet.seq_num > seq_num or new_packet.seq_num == seq_num:
                received[new_packet.seq_num] = new_packet

            while True:
                try:
                    received[seq_num]
                    seq_num += 1
                except:
                    break

    for i in range(conn.dest_seq_num, seq_num):
        packets.append(received[i])
    conn.dest_seq_num = seq_num

    return packets