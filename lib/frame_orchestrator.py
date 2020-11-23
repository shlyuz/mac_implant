import ast

from lib import yadro

destinations = {"ipi": yadro.init,
                "irk": yadro.rekey,
                "gcmd": yadro.getcmd,
                "rcmda": yadro.ack_cmds
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


def process_transport_frame(component, transport_frame):
    reply_frame = determine_destination(transport_frame, component)
    return reply_frame
