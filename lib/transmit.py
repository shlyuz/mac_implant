import pickle
import binascii
import ast
import secrets

import lib.crypto
import lib.crypto.rc6
import lib.crypto.hex_encoding
import lib.crypto.xor
import lib.crypto.asymmetric


def uncook_transmit_frame(component, frame):
    """

    :param component:
    :param frame:
    :return:
    """
    # Asymmetric Encryption Routine
    # TODO: Rotate component.inital_private_key
    frame_box = lib.crypto.asymmetric.prepare_box(component.current_private_key, component.current_lp_pubkey)
    transmit_frame = lib.crypto.asymmetric.decrypt(frame_box, frame)

    # Decoding Routine
    rc6_key = binascii.unhexlify(lib.crypto.hex_encoding.decode_hex(transmit_frame[0:44])).decode("utf-8")
    component.logging.log(f"rc6 key: {rc6_key}", level="debug", source="lib.networking")
    unxord_frame = lib.crypto.xor.single_byte_xor(transmit_frame,
                                                  component.xor_key)
    del transmit_frame
    unenc_frame = lib.crypto.hex_encoding.decode_hex(unxord_frame)
    del unxord_frame
    unsorted_recv_frame = pickle.loads(binascii.unhexlify(unenc_frame[44:]))
    del unenc_frame

    data_list = []
    sorted_frames = sorted(unsorted_recv_frame, key=lambda i: i['frame_id'])
    del unsorted_recv_frame
    for data_index in range(len(sorted_frames)):
        data_list.append(sorted_frames[data_index]['data'])

    # Symmetric decryption routine
    decrypted_data = lib.crypto.rc6.decrypt(rc6_key, data_list)
    component.logging.log(f"Decrypted data: {decrypted_data}", level="debug", source="lib.networking")

    return decrypted_data


def cook_transmit_frame(component, data):
    """

    :param component:
    :param data: encoded/encrypted data ready to transmit
    :return:
    """
    # Symmetric Encryption Routine
    rc6_key = secrets.token_urlsafe(16)
    component.logging.log(f"rc6 key: {rc6_key}", level="debug", source="lib.networking")
    transmit_data = lib.crypto.rc6.encrypt(rc6_key, str(data).encode('utf-8'))

    encrypted_frames = []
    for chunk_index in range(len(transmit_data)):
        frame_chunk = {"frame_id": chunk_index, "data": transmit_data[chunk_index],
                       "chunk_len": len(transmit_data)}
        encrypted_frames.append(frame_chunk)

    # Encoding routine
    hex_frames = binascii.hexlify(pickle.dumps(encrypted_frames))
    hex_frames = lib.crypto.hex_encoding.encode_hex(hex_frames)
    enveloped_frames = lib.crypto.xor.single_byte_xor(hex_frames,
                                                      component.xor_key)

    enveloped_frames = lib.crypto.hex_encoding.encode_hex(binascii.hexlify(rc6_key.encode("utf-8"))) + enveloped_frames
    component.logging.log(f"Unenveloped data: {enveloped_frames}", level="debug", source="lib.networking")

    # Asymmetric Encryption
    frame_box = lib.crypto.asymmetric.prepare_box(component.initial_private_key, component.current_lp_pubkey)
    transmit_frames = lib.crypto.asymmetric.encrypt(frame_box, enveloped_frames)

    component.logging.log(f"Enveloped data: {transmit_frames}", level="debug", source="lib.networking")
    return transmit_frames


def cook_sealed_frame(component, data):
    """
    Uses a nacl.public.SealedBox() to authenticate with the target component

    :param component:
    :param data:
    :return:
    """
    rc6_key = secrets.token_urlsafe(16)
    component.logging.log(f"rc6 key: {rc6_key}", level="debug", source="lib.transmit")
    transmit_data = lib.crypto.rc6.encrypt(rc6_key, str(data).encode('utf-8'))

    encrypted_frames = []
    for chunk_index in range(len(transmit_data)):
        frame_chunk = {"frame_id": chunk_index, "data": transmit_data[chunk_index],
                       "chunk_len": len(transmit_data)}
        encrypted_frames.append(frame_chunk)

    # Encoding routine
    hex_frames = binascii.hexlify(pickle.dumps(encrypted_frames))
    hex_frames = lib.crypto.hex_encoding.encode_hex(hex_frames)
    enveloped_frames = lib.crypto.xor.single_byte_xor(hex_frames,
                                                      component.xor_key)

    enveloped_frames = lib.crypto.hex_encoding.encode_hex(binascii.hexlify(rc6_key.encode("utf-8"))) + enveloped_frames
    component.logging.log(f"Unenveloped init data: {enveloped_frames}", level="debug", source="lib.transmit")

    # Asymmetric SealedBox Encryption
    lp_pubkey = component.current_lp_pubkey
    frame_box = lib.crypto.asymmetric.prepare_sealed_box(lp_pubkey)
    transmit_frames = lib.crypto.asymmetric.encrypt(frame_box, enveloped_frames)

    # Prepend the transmit frame with an init signature
    init_signature = ast.literal_eval(component.config['vzhivlyat']['init_signature'])
    transmit_frames = init_signature + transmit_frames

    component.logging.log(f"Enveloped init data: {transmit_frames}", level="debug", source="lib.transmit")
    return transmit_frames


def uncook_sealed_frame(component, frame):
    """
    Uses a nacl.public.SealedBox() to receive initialization

    :param component:
    :param frame:
    :return:
    """
    frame_box = lib.crypto.asymmetric.prepare_sealed_box(component.initial_private_key)
    transmit_frame = lib.crypto.asymmetric.decrypt(frame_box, frame)

    # Decoding Routine
    rc6_key = binascii.unhexlify(lib.crypto.hex_encoding.decode_hex(transmit_frame[0:44])).decode("utf-8")
    component.logging.log(f"rc6 key: {rc6_key}", level="debug", source="lib.transmit")
    unxord_frame = lib.crypto.xor.single_byte_xor(transmit_frame,
                                                  component.xor_key)

    del transmit_frame
    unenc_frame = lib.crypto.hex_encoding.decode_hex(unxord_frame)
    del unxord_frame
    unsorted_recv_frame = pickle.loads(binascii.unhexlify(unenc_frame[44:]))
    del unenc_frame

    data_list = []
    sorted_frames = sorted(unsorted_recv_frame, key=lambda i: i['frame_id'])
    del unsorted_recv_frame
    for data_index in range(len(sorted_frames)):
        data_list.append(sorted_frames[data_index]['data'])

    # Symmetric decryption routine
    decrypted_data = lib.crypto.rc6.decrypt(rc6_key, data_list)
    component.logging.log(f"Decrypted data: {decrypted_data}", level="debug", source="lib.transmit")

    return decrypted_data