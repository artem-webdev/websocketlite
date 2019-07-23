import socket


class BaseLoop:

    def __init__(self, **kwargs):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((kwargs["host"], kwargs["port"]))
        self.server_socket.listen()

    def run(self, websocket_class):
        while True:
            connection, address = self.server_socket.accept()
            if connection:
                websocket_class(connection, address).start()
