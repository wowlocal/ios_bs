import sys
import socket


def send_command(cmd):
    sock_file = '/tmp/daemon_ipc.sock'
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(sock_file)
    client.sendall(cmd.encode())

    result = b''
    while True:
        data = client.recv(1024)
        if data:
            result += data
        else:
            break

    client.close()
    return result.decode('utf-8')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        response = send_command(cmd)
        print(response)
    else:
        print("Usage: python client.py <command>")
