#!/usr/bin/python
import time
from daemon import runner
import socket
import os

from engine import *

class TodoDaemon(Record):
    def __init__(self):
        super(TodoDaemon, self,).__init__()
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'

        # Daemon specifications
        self.pidfile_path =  '/tmp/todo_datemon.pid'
        self.pidfile_timeout = 5

        self.socket_filename = '/tmp/todo_socket'

        if not os.path.exists(self.pidfile_path) and os.path.exists(self.socket_filename):
            os.remove(self.socket_filename)

    def run(self):
        while True:
            # Initialize socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

            # Bind the socket to the port
            sock.bind(self.socket_filename)

            # Listen for incoming connections
            sock.listen(1)

            while True:
                # Wait for a connection
                connection, client_address = sock.accept()
                res = ""

                try:
                    # Receive the data in small chunks and retransmit it
                    while True:
                        data = connection.recv(256)
                        if data:
                            connection.sendall(data)
                            res += data
                        else:
                            break

                finally:
                    # Clean up the connection
                    connection.close()
                    self.execute_task(res)

    def execute_task(self, task_string):
        task = json.loads(task_string)

        # if invalid task return doing nothing
        if not task.has_key('action'): return

        # passes message on to the correct function
        func = getattr(self, task['action'])
        task.pop('action')
        func(**task)




if __name__ == '__main__':
    daemon = TodoDaemon()
    daemon_runner = runner.DaemonRunner(daemon)
    daemon_runner.do_action()
