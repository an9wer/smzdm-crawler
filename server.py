import pickle
import socket


def server(interface, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((interface, port))
    sock.listen(1)
    print("Listening at {}".format(sock.getsockname()))
    while True:
        sc, sockname = sock.accept()
        sc.shutdown(socket.SHUT_WR)     # close write
        # TODO:
        # sc.settimeout(1)
        # sc.getsockname()
        # sc.getpeername()
        scf = sc.makefile("rb")
        data = pickle.load(scf)
        print("receive {!r}".format(data))
        sc.close()


if __name__ == "__main__":
    server("127.0.0.1", 8080)
