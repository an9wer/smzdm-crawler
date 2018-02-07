from utils.config import Config, ClientConfig, HandlerConfig, ServerConfig


def test_config():
    c = Config()
    d = {1: 2, 2: {3: 4, 5: 6}}
    c._load_from_dict(d)
    assert (
        c['1'] == 2
        and c['2'] == {3: 4, 5: 6}
        and c['2.3'] == 4
        and c["2.5"] == 6
    )


def test_client_config():
    c = ClientConfig()
    print("client:", c, sep="\r\n")


def test_handler_config():
    c = HandlerConfig()
    print("handler:", c, sep="\r\n")

def test_server_config():
    c = ServerConfig()
    print("server:", c, sep="\r\n")


if __name__ == "__main__":
    # test_config()
    test_client_config()
    test_handler_config()
    test_server_config()
