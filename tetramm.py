from enum import IntEnum
from ophyd.v2.core import Device
from ophyd.v2.epics import epics_signal_r, epics_signal_rw

class TetrammRange(IntEnum):
    uA = 0
    nA = 1

class TetrammTrigger(IntEnum):
    FreeRun = 0
    ExtTrigger = 1
    ExtBulb = 2
    ExtGate = 3

class TetrammChannels(IntEnum):
    One = 0
    Two = 1
    Four = 2

class TetrammResolution(IntEnum):
    SixteenBits = 0
    TwentyFourBits = 1
    def __repr__(self):
        match self:
            case TetrammResolution.SixteenBits:
                return '16bits'
            case TetrammResolution.TwentyFourBits:
                return '24bits'

class Tetramm(Device):
    def __init__(self, base_pv):
        self.range = epics_signal_rw(TetrammRange, base_pv + ":DRV:Range")
        self.sample_time = epics_signal_r(float, base_pv + ":DRV:SampleTime_RBV")

        self.values_per_reading = epics_signal_rw(int, base_pv + ":DRV:ValuesPerRead", base_pv + ":DRV:ValuesPerRead_RBV")
        self.averaging_time = epics_signal_rw(float, base_pv + ":DRV:AveragingTime", base_pv + ":DRV:AveragingTime_RBV")
        self.to_average = epics_signal_r(int, base_pv + ":DRV:NumAverage_RBV")
        self.averaged = epics_signal_r(int, base_pv + ":DRV:NumAveraged_RBV")

        self.acquire = epics_signal_rw(bool, base_pv + ":DRV:Acquire")

        self.overflows = epics_signal_r(int, base_pv + ":DRV:RingOverflows")

        self.channels = epics_signal_rw(TetrammChannels, base_pv + ":DRV:NumChannels")
        self.resolution = epics_signal_rw(TetrammResolution, base_pv + ":DRV:Resolution")
        self.trigger = epics_signal_rw(TetrammTrigger, base_pv + ":DRV:TriggerMode")
        self.bias = epics_signal_rw(bool, base_pv + ":DRV:BiasState")
        self.bias_volts = epics_signal_rw(float, base_pv + ":DRV:BiasVoltage", base_pv + ":DRV:BiasVoltage_RBV")
