from ophyd_epics_devices.panda import PandA
from ophyd.v2.core import DeviceCollector
from ophyd_epics_devices.panda import PandA

def panda(name="pnda") -> PandA:
    with DeviceCollector():
        pnda = PandA("TS-PANDA")
    return pnda
