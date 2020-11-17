import socket
import sys
import struct


class Transport:
    def __init__(self):
        self.info = {"name": "rev_tcp_socket",
                     "author": "Und3rf10w",
                     "desc": "Connect to a tcp socket and use that as a transport, inverse of bind_tcp_socket",
                     "version": "0.01-dev"
                     }
        # Should always be initialized here
        self.config = {}
        self.connect_addr = "127.0.0.1"  # default
        self.connect_port = 8084  # default
        self.trans_sock = None
        self.conn_sock = None
        self.logging = None

    def prep_transport(self, transport_config):
        self.config = transport_config
        self.logging = transport_config['logging']
        self.connect_addr = self.config['bind_addr']
        self.connect_port = self.config['bind_port']
        self.trans_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.logging.log(f"Attempting to connect to to {self.connect_addr}: {self.connect_port}", source=self.info['name'])
            self.trans_sock.connect((self.connect_addr, int(self.connect_port)))
            self.logging.log(f"Transport prepared", level="debug", source=self.info['name'])
            return 0
        except Exception as e:
            self.logging.log(f"[{type(e).__name__}]: {e}", level="error", source=self.info['name'])

    def send_data(self, data):
        # Here you're going to take cooked data and send it over whatever your transport mechanism is. Return 0 in
        #   case of success.
        # Your transport should not transmit NOOPs unless its used for a connectivity check
        slen = struct.pack('<I', len(data))
        self.conn_sock.sendall(slen)
        self.conn_sock.sendall(data)
        return 0

    def recv_data(self):
        # Here you're going to return the cooked data you retrieved from your transport.
        # Your transport should NOT receive NOOPs unless its used for a connectivity check.
        # TODO: bugchecks, error handling
        frame_size = self.conn_sock.recv(4)
        slen = struct.unpack('<I', frame_size)[0]
        frame = self.conn_sock.recv(slen)
        return frame
