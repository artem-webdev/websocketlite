import random
import hashlib
import base64
import uuid


class Protocol:
    const_chang_key = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    data_type_read_header = {
        0: "fragmented_message",
        1: "text",
        2: "binary",
        3: "reserve_data",
        8: "close_connect",
        9: "ping",
        10: "pong",
        11: "reserve_op_code"
    }

    data_type_make_header = dict([v, k] for k, v in data_type_read_header.items())

    def is_ready_headers_handshake(self, data_bytes):
        str_data = data_bytes.decode()
        if "\r\n\r\n" in str_data:
            if "Sec-WebSocket-Key" in str_data:
                return True
            elif "Sec-WebSocket-Accept" in str_data:
                return True

    def get_key_handshake(self, utf8_str, in_head):
        headers_list = utf8_str.split("\r\n")
        for header in headers_list:
            if in_head in header:
                return header.split(":")[1].strip()

    def make_response_handshake(self, bytes_data):
        data_str = bytes_data.decode()
        key = self.get_key_handshake(data_str, "Sec-WebSocket-Key")
        key_response = self.make_key_response_handshake(key)
        headers = [
            "HTTP/1.1 101 Switching Protocols\r\n",
            "Upgrade: websocket\r\n",
            "Connection: Upgrade\r\n",
            f"Sec-WebSocket-Accept: {key_response}\r\n\r\n"
        ]
        return "".join(headers).encode()

    def make_key_response_handshake(self, key_request):
        str_key = key_request + self.const_chang_key
        hash_key = hashlib.sha1(str_key.encode()).digest()
        res_key = base64.b64encode(hash_key).decode()
        return res_key

    def make_key_request_handshake(self):
        return base64.b64encode(uuid.uuid4().bytes).decode()

    def make_request_handshake(self, host, key, patch="/"):
        headers = [
            f"GET {patch} HTTP/1.1\r\n",
            f"Host: {host}\r\n",
            "Connection: Upgrade\r\n",
            "Upgrade: websocket\r\n",
            "Sec-WebSocket-Version: 13\r\n\r\n",
            f"Sec-WebSocket-Key: {key}\r\n"
        ]
        return "".join(headers).encode()

    def request_handshake(self):
        pass

    @property
    def get_mask_key(self):
        return random.randint(2147483648, 4294967295)

    def decode_mask(self, payload, mask):
        payload_decode = bytearray()
        for i in range(len(payload)):
            payload_decode.append(payload[i] ^ mask[i % 4])
        return payload_decode

    def encode_mask(self, payload):
        mask_payload = bytearray()
        mask = int(self.get_mask_key).to_bytes(4, byteorder='big')
        for i in range(len(payload)):
            mask_payload.append(payload[i] ^ mask[i % 4])
        return mask + mask_payload

    def get_count_bytes_for_read_header(self, byte):

        count = byte & 127
        if count <= 125:
            if byte > 127:
                return 6
            else:
                return 2
        elif count == 126:
            if byte > 127:
                return 8
            else:
                return 4
        elif count == 127:
            if byte > 127:
                return 14
            else:
                return 10

    def get_header(self, headers_bytes):

        start_bytes_payload = 0

        len_payload_header = headers_bytes[1] & 127

        fin = 0
        if headers_bytes[0] >= 128:
            fin = 1

        data_type_header = headers_bytes[0] & 15
        data_type = self.data_type_read_header[data_type_header]

        is_mask = 0
        if headers_bytes[1] > 127:
            is_mask = 1

        len_payload = 0
        mask = bytearray()
        if len_payload_header <= 125:
            len_payload = len_payload_header
            if is_mask:
                mask = headers_bytes[2:6]
                start_bytes_payload = 6
            else:
                start_bytes_payload = 2

        elif len_payload_header == 126:
            len_payload = int.from_bytes(headers_bytes[2:4], byteorder='big')
            if is_mask:
                mask = headers_bytes[4:8]
                start_bytes_payload = 8
            else:
                start_bytes_payload = 4
        elif len_payload_header == 127:
            len_payload = int.from_bytes(headers_bytes[2:10], byteorder='big')
            if is_mask:
                mask = headers_bytes[10:14]
                start_bytes_payload = 14
            else:
                start_bytes_payload = 10

        return {
            "fin": fin,
            "is_mask": is_mask,
            "len_payload_bytes": len_payload,
            "data_type": data_type,
            "start_bytes_payload": start_bytes_payload,
            "bytes_mask": mask
        }

    def decode(self, bytes_stream, headers):

        if headers["is_mask"]:
            return self.decode_mask(bytes_stream[headers["start_bytes_payload"]:], headers["bytes_mask"])
        else:
            return bytes_stream[headers["start_bytes_payload"]:]

    def set_header(self, len_payload, is_mask=0, data_type="text", is_fin=1):

        len_payload_header = 0
        if len_payload <= 125:
            len_payload_header = len_payload
        elif len_payload > 125:
            len_payload_header = 126
        elif len_payload > 65535:
            len_payload_header = 127

        data_type_header = int(self.data_type_make_header[data_type])

        if is_fin:
            fin_end_data_type_header = data_type_header | 128
        else:
            fin_end_data_type_header = data_type_header | 0

        if is_mask:
            mask_and_len_payload_header = len_payload_header | 128
        else:
            mask_and_len_payload_header = len_payload_header | 0

        encode_headers = bytearray()
        encode_headers.append(fin_end_data_type_header)
        encode_headers.append(mask_and_len_payload_header)

        if len_payload > 125 and len_payload <= 65535:
            encode_headers.extend(int(len_payload).to_bytes(2, byteorder='big'))
        elif len_payload > 65535:
            encode_headers.extend(int(len_payload).to_bytes(8, byteorder='big'))

        return encode_headers

    def encode(self, payload, is_mask=0, data_type="text", is_fin=1):
        len_payload = len(payload)
        header = self.set_header(len_payload, is_mask, data_type, is_fin)
        if is_mask:
            payload_and_mask = self.encode_mask(payload)
            return header + payload_and_mask
        else:
            return header + payload
