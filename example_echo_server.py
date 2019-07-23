from websocketlite.loop import BaseLoop
from websocketlite.handlers import ThreadWebsocketHandlerServer


class EchoWebSocketServer(ThreadWebsocketHandlerServer):

    def on_open(self):
        print("WebSocket opened")

    def on_message(self, message):
        print("WebSocket on message")
        self.write_message(message)

    def on_close(self):
        print("WebSocket closed")


loop = BaseLoop(host="ws://localhost", port=9000)
loop.run(EchoWebSocketServer)
