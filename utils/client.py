import pickle
import socket

from utils.config import ClientConfig


CONFIG = ClientConfig()
assert isinstance(CONFIG["interveal"], int)


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
        self.sock.shutdown(socket.SHUT_RD)   # close read

    def close(self):
        self.sock.close()

    def _prepare(self):
        data = {
            "search": CONFIG["search"],
            "interveal": CONFIG["interveal"],
        }
        return pickle.dumps(data)

    def request(self):
        data = self._prepare()
        self.sock.sendall(data)

    def __call__(self):
        try: self.request()
        finally: self.close()
