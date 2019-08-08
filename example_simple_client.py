from websocketlite.handlers import ThreadWebsocketHandlerClient


class WebsocketClient(ThreadWebsocketHandlerClient):

    def on_open(self):
        print("websocket on open!")

    def on_message(self, message):
        print("WebSocket on message")
        self.write_message(message)

    def on_close(self):
        print("websocket closet!")


ws = WebsocketClient(host="ws://localhost", port=9000)
ws.start()
