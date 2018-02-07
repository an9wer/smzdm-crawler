import pickle
import socket

from functools import partial
from utils.config import ClientConfig


CONFIG = ClientConfig()
assert isinstance(CONFIG["interval"], int)


class Client:

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM

    def __init__(self, connect=True):
        self.host = CONFIG["host"]
        self.port = CONFIG["port"]
        self.server_address = (self.host, self.port)

        self.sock = socket.socket(self.address_family, self.socket_type)

        if connect: self.connect() 

    def connect(self):
        self.sock.connect(self.server_address)
        #self.sock.shutdown(socket.SHUT_RD)   # close read

    def close(self):
        self.sock.close()

    def _prepare(self):
        data = {
            "search": CONFIG["search"],
            "interval": CONFIG["interval"],
        }
        return pickle.dumps(data)

    def recv_all(self):
        """
        data = b""
        while True:
            msg = self.sock.recv(1024)
            if msg == b"":
                break
            data += msg
        return data
        """
        return b"".join(iter(partial(self.sock.recv, 1024), b""))

    def request(self):
        data = self._prepare()
        self.sock.sendall(data)
        msg = self.recv_all()
        print(msg)

    def __call__(self):
        try: self.request()
        finally: self.close()
