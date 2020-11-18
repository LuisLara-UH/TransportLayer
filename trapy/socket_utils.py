import socket

sender_socket_protocol = socket.IPPROTO_RAW
receiver_socket_protocol = socket.IPPROTO_TCP

def create_sender_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

    return sock

def create_receiver_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    return sock
