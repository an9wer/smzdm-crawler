import pickle
import socket


def client(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.shutdown(socket.SHUT_RD)   # close read
    print("Client has been assigned socket name {}".format(sock.getsockname()))
    data = pickle.dumps(list(range(10000000)))
    sock.sendall(data)
    sock.close()


if __name__ == "__main__":
    client("127.0.0.1", 8080)
