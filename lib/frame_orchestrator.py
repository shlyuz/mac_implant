import ast

from lib import yadro
from lib import transmit

destinations = {"ipi": yadro.init,
                "irk": yadro.rekey,
                "gcmd": yadro.getcmd
                }


def determine_destination(frame, component):
    if frame['cmd'] in destinations.keys():
        component.logging.log(f"Routing '{frame['cmd']}' frame to {destinations[frame['cmd']]}", level="debug",
                              source="lib.frame_orchestrator")
        return destinations[frame['cmd']](frame, component)
    else:
        component.logging.log(f"Invalid frame received", level="warn", source="lib.frame_orchestrator")
        component.logging.log(f"Invalid frame: {frame}", level="debug", source="lib.frame_orchestrator")
        return None


def process_transport_frame(component, reply_frame):
    uncooked_frame = ast.literal_eval(transmit.uncook_transmit_frame(component, reply_frame).decode('utf-8'))
    reply_frame = determine_destination(uncooked_frame, component)
    return reply_frame
