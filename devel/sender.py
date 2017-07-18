import socket, os, sys


server_address = '/tmp/todo_socket'

# Create a UDS socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

print 'connecting to %s' % server_address

try:
    sock.connect(server_address)
except socket.error, msg:
    print msg
    sys.exit(1)

try:
    # Send data
    message = "penises " * 9001
    print message

    print 'sending "%s"' % message
    sock.sendall(message)

    amount_received = 0
    amount_expected = len(message)

    while amount_received < amount_expected:
        data = sock.recv(256)
        amount_received += len(data)
        print 'received "%s"' % data

except Exception as e:
    raise e

finally:
    print 'closing socket'
    sock.close()
