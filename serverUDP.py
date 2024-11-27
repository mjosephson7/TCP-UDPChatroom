# to run in terminal: python serverUDP.py
from chatroom import ServerUDP
server = ServerUDP(12345)
server.run()