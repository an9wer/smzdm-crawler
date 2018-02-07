from utils.server import Server


def test_server():
    s = Server()
    s.server_forever()


if __name__ == "__main__":
    test_server()
