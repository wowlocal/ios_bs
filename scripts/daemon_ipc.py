import os
import sys
import socket
import subprocess
import daemon
from daemon import pidfile


def handle_client_connection(conn):
    while True:
        try:
            data = conn.recv(1024)
            if data:
                cmd = data.decode('utf-8')
                if cmd.lower() == 'exit':
                    break
                else:
                    try:
                        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
                        conn.sendall(result)
                    except subprocess.CalledProcessError as e:
                        conn.sendall(str(e).encode())
            else:
                break
        except Exception as e:
            conn.sendall(str(e).encode())
            break


def main():
    sock_file = '/tmp/daemon_ipc.sock'

    if os.path.exists(sock_file):
        os.remove(sock_file)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock_file)
    server.listen(5)

    while True:
        conn, _ = server.accept()
        handle_client_connection(conn)
        conn.close()


if __name__ == "__main__":
    with daemon.DaemonContext(
        working_directory=os.getcwd(),
        umask=0o002,
        pidfile=pidfile.TimeoutPIDLockFile('/tmp/daemon_ipc.pid')
    ):
        main()

