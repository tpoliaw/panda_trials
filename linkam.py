from ophyd.v2.core import Device
from ophyd.v2.epics import epics_signal_rw, epics_signal_r


class Linkam(Device):
    def __init__(self, base_pv: str):
        self.set_point = epics_signal_rw(
            float, base_pv + ":SETPOINT", base_pv + ":SETPOINT:SET"
        )
        self.temp = epics_signal_r(float, base_pv + ":TEMP")
        self.ramp_rate = epics_signal_rw(
            float, base_pv + ":RAMPRATE", base_pv + ":RAMPRATE:SET"
        )
        self.ramp_time = epics_signal_r(float, base_pv + ":RAMPTIME")
        self.start_heat = epics_signal_rw(float, base_pv + ":STARTHEAT")
        self.dsc = epics_signal_r(bool, base_pv + ":DSC")
