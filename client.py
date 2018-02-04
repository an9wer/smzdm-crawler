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


class Client:

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM

    def __init__(self, host, port, connect=True):
        self.host = host
        self.port = port
        self.server_address = (host, port)

        self.sock = socket.socket(self.address_family, self.socket_type)

        if connect: self.connect() 

    def connect(self):
        self.sock.connect(self.server_address)
        self.sock.shutdown(socket.SHUT_RD)   # close read

    def close(self):
        self.sock.close()

    def _prepare(self):
        # TODO
        data = pickle.dumps([1, 2, 3])
        return data

    def request(self):
        data = self._prepare()
        self.sock.sendall(data)

    def __call__(self):
        try: self.request()
        finally: self.close()


if __name__ == "__main__":
    #client("127.0.0.1", 8080)
    c = Client("127.0.0.1", 8080)
    c()
