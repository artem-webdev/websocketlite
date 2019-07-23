from .mixins import BaseHandlerMixin
from threading import Thread
import socket
from concurrent.futures import ThreadPoolExecutor


class ThreadWebsocketHandlerServer(Thread, BaseHandlerMixin):

    def __init__(self, connect, addr):
        super().__init__()

        self.connect = connect
        self.addr = addr

        self.buffer = bytearray()
        self.tail_data = bytearray()
        self.body = bytearray()
        self.max_len_text_body = 10000
        self.is_handshake = False
        self.count_bytes_for_headers = 0
        self.is_read_header = False
        self.headers_info = None
        self.is_pong = False

        self.brake = False

    def _set_handshake(self):
        if self.protocol.is_ready_headers_handshake(self.buffer):
            headers_handshake = self.protocol.make_response_handshake(self.buffer)
            self.connect.sendall(headers_handshake)
            self.buffer = bytearray()
            self.is_handshake = True
            self.on_open()

    def _valid_len_text_message(self):
        if self.is_read_header and self.headers_info["data_type"] == "text":
            if self.headers_info["len_payload_bytes"] > self.max_len_text_body:
                self.close("error max len message - 10kb !")
                self.connect.close()
                self.brake = True

    def run(self):

        while True:
            if self.brake:
                break
            try:
                data = self.connect.recv(4096)
                if not data:
                    break
                else:
                    self._write_buffer(data)
                    if not self.is_handshake:
                        self._set_handshake()
                    else:
                        self._set_count_bytes_for_headers()
                        self._read_headers()
                        self._valid_len_text_message()
                        self._parse_body()
            except (BrokenPipeError, ConnectionResetError):
                self.on_close()
                self.connect.close()
                break


class BaseThreadWebsocketHandlerClient(Thread, BaseHandlerMixin):
    threads_pool = []

    def __init__(self):
        super().__init__()

        self.connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = None
        self.port = None

        self.buffer = bytearray()
        self.body = bytearray()
        self.max_len_text_body = 10000
        self.is_handshake = False
        self.count_bytes_for_headers = 0
        self.is_read_header = False
        self.headers_info = None
        self.is_pong = False
        self.brake = False
        self.request_key = None

        self.count_write_thread_poll = 1000

    def connection(self):
        try:
            self.connect.connect((self.host, self.port))
        except (BaseException,) as error:
            raise

    def request_handshake(self):
        self.request_key = self.protocol.make_key_request_handshake()
        headers_handshake = self.protocol.make_request_handshake(self.host, self.request_key)
        self.connect.sendall(headers_handshake)

    def _set_handshake(self):
        if self.protocol.is_ready_headers_handshake(self.buffer):
            response_key = self.protocol.get_key_handshake(self.buffer.decode(), "Sec-WebSocket-Accept")
            res_key = self.protocol.make_key_response_handshake(self.request_key)
            if res_key == response_key:
                self.buffer = bytearray()
                self.is_handshake = True
                self.on_open()

    def write_message(self, message):
        bytes_body = self.protocol.encode(message.encode())
        with ThreadPoolExecutor(self.count_write_thread_poll) as pool:
            pool.map(self.connect.sendall, [bytes_body])

    def run(self):
        self.connection()
        self.request_handshake()
        while True:
            try:
                data = self.connect.recv(4096)
                if not data:
                    break
                else:
                    self._write_buffer(data)
                    if not self.is_handshake:
                        self._set_handshake()
                    else:
                        self._set_count_bytes_for_headers()
                        self._read_headers()
                        self._parse_body()
            except (BrokenPipeError, ConnectionResetError):
                self.on_close()
                self.connect.close()
                break


class ThreadWebsocketHandlerClient(BaseThreadWebsocketHandlerClient):
    def __init__(self, **kwargs):
        super().__init__()
        self.host = kwargs["host"]
        self.port = kwargs["port"]
