import json


_sentinel = object()


class Config(dict):

    def __init__(self, path=_sentinel):
        self.load_from_json(path)

    def _load_from_dict(self, d, prefix=_sentinel):
        for k, v in d.items():
            if prefix is not _sentinel:
                _prefix = str(prefix) + "." + str(k)
            else:
                _prefix = str(k)

            self[_prefix] = v
            if isinstance(v, dict):
                self._load_from_dict(v, prefix=_prefix)
    
    def load_from_json(self, path=_sentinel):
        if path is _sentinel:
            path = self.default_path
        with open(path, 'r') as f:
            self._load_from_dict(json.load(f))


class ClientConfig(Config):

    default_path = "client.json"


class HandlerConfig(Config):

    default_path = "handler.json"


class ServerConfig(Config):

    default_path = "server.json"
