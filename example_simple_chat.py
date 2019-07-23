from websocketlite.loop import BaseLoop
from websocketlite.handlers import ThreadWebsocketHandlerServer


class SimpleChatWebSocketServer(ThreadWebsocketHandlerServer):
    connections = []

    def on_open(self):
        print("WebSocket opened")
        self.connections.append(self.connect)

    def on_message(self, message):
        self.broadcast(message)

    def broadcast(self, message):
        for connect in self.connections:
            if connect != self.connect:
                self.write_message(message, connect)

    def on_close(self):
        self.connections.remove(self.connect)
        print("WebSocket closed")


loop = BaseLoop(host="ws://localhost", port=9000)
loop.run(SimpleChatWebSocketServer)
