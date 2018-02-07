import pickle
import socket

from utils.handler import Handler
from utils.config import ServerConfig


CONFIG = ServerConfig()


class Server:

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1
    allow_reuse_address = True

    def __init__(self, bind_and_activate=True):
        self.addr = CONFIG["addr"]
        self.port = CONFIG["port"]
        self.server_address = (self.addr, self.port)
        self.handler = Handler


        self.sock = socket.socket(self.address_family, self.socket_type)

        if bind_and_activate:
            try:
                self.bind()
                self.active()
            except:
                self.close()
                raise

    def bind(self):
        if self.allow_reuse_address:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.server_address)
        self.server_address = self.sock.getsockname()
        print("Listening at {}".format(self.server_address))

    def active(self):
        self.sock.listen(self.request_queue_size)

    def close(self):
        self.sock.close()

    def accept(self):
        return self.sock.accept()

    def server_forever(self):
        try:
            while True:
                self.handle_connection()
        finally:
            self.close()

    def handle_connection(self):
        connection, client_address = self.accept()
        connection.shutdown(socket.SHUT_WR)     # close wirte

        if self.verify_connection(client_address):
            try:
                self._handle_connection(connection)
            except Exception:
                raise
                # TODO: handle error (log)
                # self.handle_error(connection)
                self.close_connection(connection)
            except:
                self.close_connection(connection)
                raise
        else:
            self.close_connection(connection)

    def _handle_connection(self, connection):
        con_file = connection.makefile("rb")
        data = pickle.load(con_file)
        print("receive {!r}".format(data))
        search = data.get("search")
        interveal = data.get("interveal", 3600)
        assert search
        self.handler(search, interveal)()
        #self.schedule.enter(interveal, 1, self.handler, argument=(search,))

    def verify_connection(self, address):
        return True

    def close_connection(self, connection):
        connection.close()


if __name__ == "__main__":
    s = Server("127.0.0.1", 8080)
    s.server_forever()
