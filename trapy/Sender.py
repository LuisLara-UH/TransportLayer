from socket_trapy import dial, send, close

address = 'localhost:8080'
connection = dial(address)
#close(connection)
print('Dialed')

while True:
    message = bytes(input(), "utf8")
    if message == b'exit':
        break
    sent = send(connection, message)
    print(str(sent) + ' sent')

close(connection)