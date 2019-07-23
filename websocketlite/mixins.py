from .web_socket_protocol import Protocol


class BaseHandlerMixin:
    protocol = Protocol()

    def _write_buffer(self, data):
        self.buffer += data

    def _reset_buffer(self):
        self.buffer = bytearray()

    def ping(self, ping_message):
        self.is_pong = False
        ping_payload = self.protocol.encode(ping_message.encode(), 0, "ping")
        self.connect.sendall(ping_payload)

    def write_message(self, message, connect=None):
        try:
            if not connect:
                bytes_body = self.protocol.encode(message.encode())
                self.connect.sendall(bytes_body)
            else:
                bytes_body = self.protocol.encode(message.encode())
                connect.sendall(bytes_body)
        except:
            raise Exception("error send message!")



    def close(self, message):
        self.connect.sendall(self.protocol.encode(message.encode(), 0, "close_connect"))

    def on_pong(self, pong_message):
        pass

    def on_open(self):
        raise NotImplementedError("Определите on_open в {}.".format(self.__class__.__name__))

    def on_close(self):
        raise NotImplementedError("Определите on_close в {}.".format(self.__class__.__name__))

    def on_message(self, message):
        raise NotImplementedError("Определите on_message в {}.".format(self.__class__.__name__))

    def _set_count_bytes_for_headers(self):
        if not self.count_bytes_for_headers:
            self.count_bytes_for_headers = self.protocol.get_count_bytes_for_read_header(self.buffer[1])

    def _read_headers(self):
        if not self.is_read_header:
            if len(self.buffer) >= self.count_bytes_for_headers:
                self.headers_info = self.protocol.get_header(
                    self.buffer[0:self.count_bytes_for_headers])
                self.is_read_header = True

    def _parse_body(self):
        if self.is_read_header:
            len_pkg = (self.count_bytes_for_headers + self.headers_info["len_payload_bytes"])
            if len(self.buffer) >= len_pkg:
                self.body = self.protocol.decode(self.buffer[:len_pkg], self.headers_info)
                self.count_bytes_for_headers = 0
                self.is_read_header = False
                self.buffer = self.buffer[len_pkg:]

                if self.headers_info["fin"]:

                    if self.headers_info["data_type"] == "text":
                        self.on_message(self.body.decode())

                    if self.headers_info["data_type"] == "ping":
                        pong_payload = self.protocol.encode("pong".encode(), 0, "pong")
                        self.connect.sendall(pong_payload)

                    elif self.headers_info["data_type"] == "pong":
                        self.is_pong = True
                        self.on_pong(self.body.decode())

                    elif self.headers_info["data_type"] == "close_connect":
                        self.on_close()
                        self.close("closed")
                        self.connect.close()
                        self.brake = True
