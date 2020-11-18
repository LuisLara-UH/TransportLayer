from socket_trapy import listen, accept, recv, close

address = 'localhost:8080'
listen_connection = listen(address)
connection = accept(listen_connection)
print('Connection accepted')

data = str(recv(connection, 100), "utf8")
while not data == '':
    print(str(data))
    data = str(recv(connection, 100), "utf8")

close(connection)