import pickle
import socket
import threading

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
        self.handlers = []

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

    def handle_error(self, connection, error):
        err_msg = "some error happens: {!r}".format(error)
        connection.sendall(err_msg)


    def handle_connection(self):
        connection, client_address = self.accept()
        #connection.shutdown(socket.SHUT_WR)     # close wirte

        if self.verify_connection(client_address):
            try:
                self._handle_connection(connection)
            except Exception as e:
                self.handle_error(connection)
            except:
                self.handle_error(connection)
                raise
            else:
                connection.sendall(b"action now!")
            finally:
                self.close_connection(connection)
        else:
            self.close_connection(connection)

    def _handle_connection(self, connection):
        # cancel existed job
        for handler in self.handlers:
            handler.state = "cancel"
        self.handlers.clear()
        # create a new job
        con_file = connection.makefile("rb")
        data = pickle.load(con_file)
        print("receive {!r}".format(data))
        search = data.get("search")
        interval = data.get("interval")
        handler = self.handler(search, interval)
        thread = threading.Thread(target=handler)
        thread.start()
        self.handlers.append(handler)

    def verify_connection(self, address):
        return True

    def close_connection(self, connection):
        connection.close()


if __name__ == "__main__":
    s = Server("127.0.0.1", 8080)
    s.server_forever()
