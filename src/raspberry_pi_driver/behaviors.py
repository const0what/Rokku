import json
from time import sleep
from src.raspberry_pi_motion_sensor.motion_interface import MotionPIR

def sample(msg_q, pub) -> None:
    """
    A sample behavior upon getting message form msg_q. This function can ONLY
    be called if there is something in the msg_q already. Sample behavior
    prints out the received message, and send back a message containing the
    same content.

    Args:
        msg_q:      The queue connecting this process to listen_proc
        pub:        Publisher for publishing MQTT message
    Returns:
        None
    Raises:
        None
    """
    msg: str = msg_q.get()
    print(f"Sample behavior received: {msg}")
    identifier, flag = json.loads(msg)
    sleep(1)
    pub.publish(json.dumps([identifier, flag]))

def motion(pub, flag):
    motion = MotionPIR(None, 23)
    if flag is True:
        motion.set_armed()
    else:
        motion.set_disarmed()
    pub.publish(json.dumps(["motion", motion.get_state()]))

