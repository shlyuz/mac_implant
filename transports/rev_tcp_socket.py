import socket
import sys
import struct
from time import sleep


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
        self.logging = None
        self.component_id = None

    def prep_transport(self, transport_config):
        self.config = transport_config
        self.component_id = transport_config['transport_id']
        self.logging = transport_config['logging']
        self.connect_addr = self.config['connect_addr']
        self.connect_port = int(self.config['connect_port'])
        self.trans_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.trans_sock.settimeout(300)
        try:
            self.logging.log(f"Attempting to connect to to {self.connect_addr}: {self.connect_port}", source=self.info['name'])
            self.trans_sock.connect((self.connect_addr, int(self.connect_port)))
            self.logging.log(f"Transport prepared", level="debug", source=self.info['name'])
            return 0
        except ConnectionRefusedError:
            from time import sleep
            sleep(10)
            self.trans_sock.connect((self.connect_addr, int(self.connect_port)))
            return 0
        except Exception as e:
            self.logging.log(f"[{type(e).__name__}]: {e}", level="error", source=self.info['name'])

    def reconnect_socket(self):
        self.trans_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.trans_sock.connect((self.connect_addr, self.connect_port))

    def send_data(self, data):
        # Here you're going to take cooked data and send it over whatever your transport mechanism is. Return 0 in
        #   case of success.
        # Your transport should not transmit NOOPs unless its used for a connectivity check
        slen = struct.pack('<I', len(data))
        try:
            self.trans_sock.sendall(slen)
            self.trans_sock.sendall(data)
        except BrokenPipeError or socket.error or ConnectionResetError:
            self.reconnect_socket()
            sleep(2)
            self.trans_sock.sendall(slen)
            self.trans_sock.sendall(data)
        return 0

    def recv_data(self):
        # Here you're going to return the cooked data you retrieved from your transport.
        # Your transport should NOT receive NOOPs unless its used for a connectivity check.
        # TODO: bugchecks, error handling
        try:
            try:
                frame_size = self.trans_sock.recv(4)
                if frame_size == b'':
                    raise ConnectionResetError
            # except ConnectionResetError or BrokenPipeError:
            #     self.trans_sock.close()
            #     self.reconnect_socket()
            #       frame_size = self.trans_sock.recv(4)
            except BrokenPipeError or ConnectionResetError:
                self.trans_sock.close()
                self.reconnect_socket()
            except Exception as e:
                if e.errno == 54:  # Connection reset by peer, not sure why this is happening, we're out of sync with the LP. Will reset when socket time out is hit
                    self.trans_sock.close()
                    self.reconnect_socket()
                    self.trans_sock.send(b'')
                    frame_size = self.trans_sock.recv(4)
                self.logging.log(f"Critical [{type(e).__name__}] when recv_data: {e}",
                                 level="critical")
            slen = struct.unpack('<I', frame_size)[0]
            frame = self.trans_sock.recv(slen)
            # self.reconnect_socket()
            return frame
        except ConnectionResetError or UnboundLocalError or TimeoutError or OSError or socket.error:
            self.reconnect_socket()
            try:
                frame_size = self.trans_sock.recv(4)
                if frame_size == b'':
                    raise ConnectionResetError
            # except ConnectionResetError or BrokenPipeError:
            #     self.trans_sock.close()
            #     self.reconnect_socket()
            #       frame_size = self.trans_sock.recv(4)
            except BrokenPipeError or ConnectionResetError:
                self.trans_sock.close()
                self.reconnect_socket()
            except Exception as e:
                self.logging.log(f"Critical [{type(e).__name__}] when recv_data: {e}",
                                 level="critical")
            slen = struct.unpack('<I', frame_size)[0]
            frame = self.trans_sock.recv(slen)
            # self.reconnect_socket()
            return frame
        except struct.error as e:
            self.logging.log(f"invalid struct {e}", level="debug")
        except Exception as e:
            self.logging.log(f"Critical [{type(e).__name__}] when recv_data: {e}",
                                 level="critical")
