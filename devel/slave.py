import socket
import os

server_address = '/tmp/todo_socket'

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

os.remove(server_address)
# Bind the socket to the port
# print 'starting up on %s' % server_address
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    # print 'waiting for a connection'
    connection, client_address = sock.accept()
    try:
        print 'connection from', client_address

        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(256)
            print 'received "%s"' % data
            if data:
                print 'sending data back to the client'
                connection.sendall(data)
            else:
                print 'no more data from', client_address
                break

    finally:
        # Clean up the connection
        connection.close()
