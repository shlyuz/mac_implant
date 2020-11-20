import random
import string
import uuid
import configparser
import pickle


import lib.crypto.asymmetric
import lib.crypto.rc6
import lib.crypto.xor


def generate_private_key():
    return lib.crypto.asymmetric.generate_private_key()


rc6_key = input(f"Listening post: [crypto/sym_key]: ")
xor_key = input(f"Listening post: [crypto/xor_key]: ")
lp_pubkey = input(f"Listening post's pubkey: ")
implant_id = input(f"Vzhivlyat ID: ")
transport_name = input(f"Transport name: ")
task_check_time = input(f"task_check_time time: ")
init_signature = input(f"init_signature: ")
private_key = generate_private_key()

print(f"Implant configuration:")
print(f"[vzhivlyat][id]: {implant_id}")
print(f"[vzhivlyat][task_check_time]: {task_check_time}")
print(f"[vzhivlyat][transport_name]: {transport_name}")
print(f"[vzhivlyat][init_signature]: {init_signature}")
print(f"[crypto][implant_pubkey]: {private_key.public_key}")
print(f"[crypto][lp_pk]: {lp_pubkey}")
print(f"[crypto][sym_key]: {rc6_key}")
print(f"[crypto][xor_key]: {xor_key}")
print(f"[crypto][priv_key]: {private_key}")

config = configparser.RawConfigParser()
config.add_section("vzhivlyat")
config.set("vzhivlyat", "id", implant_id)
config.set("vzhivlyat", "transport_name", transport_name)
config.set("vzhivlyat", "task_check_time", task_check_time)
config.set("vzhivlyat", "init_signature", init_signature)

config.add_section("crypto")
config.set("crypto", "lp_pk", lp_pubkey)
config.set("crypto", "sym_key", rc6_key)
config.set("crypto", "xor_key", xor_key)
config.set("crypto", "priv_key", private_key)

# Write unencrypted configuration
with open("shlyuz.conf", "w+") as unencrypted_configfile:
    config.write(unencrypted_configfile)


# Write encrypted configuration
config_encryption_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
print(f"Configuration encryption key: {lib.crypto.xor.single_byte_xor(config_encryption_key.encode('utf-8'), 0x69)}")

with open("shlyuz.conf", "rb+") as configfile:
    config_bytes = configfile.read()
    encrypted_contents = lib.crypto.rc6.encrypt(config_encryption_key, config_bytes)
    pickled_encrypted = pickle.dumps(encrypted_contents)
    encoded_contents = lib.crypto.xor.single_byte_xor(pickled_encrypted, 0x69)
    configfile.seek(0)
    configfile.write(encoded_contents)

# # Decryption routine
# def read_encrypted_config():
#     with open("shlyuz_rev_tcp_socket.conf", "rb+") as configfile:
#         config_bytes = configfile.read()
#         decoded_content = lib.crypto.xor.single_byte_xor(config_bytes, 0x69)
#         pickled_decoded = pickle.loads(decoded_content)
#         decrypted_contents = lib.crypto.rc6.decrypt(config_encryption_key, pickled_decoded)
#         decrypted_config = decrypted_contents.decode('utf-8')
#     return decrypted_config
#
# # Loading routine
# def loading():
#     config = configparser.RawConfigParser()
#     config.read_string(read_encrypted_config())
#     return config

# config = loading()
