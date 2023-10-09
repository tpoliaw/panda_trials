from enum import IntEnum
from ophyd.v2.core import Device, wait_for_value
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
                return "16bits"
            case TetrammResolution.TwentyFourBits:
                return "24bits"


class TetrammGeometry(IntEnum):
    Diamond = 0
    Square = 1


class Tetramm(Device):
    base_sample_rate: int
    """base rate"""

    maximum_readings_per_frame: int
    """An upper limit on the dimension of frames collected during a collection"""

    minimum_values_per_reading: int
    """A lower bound on the number of values that will be averaged to create a single reading"""

    idle_acquire: bool
    """Whether the tetramm should be left acquiring after a collection"""

    idle_trigger_state: TetrammTrigger
    """The state the trigger should be left in when no collection is running"""

    def __init__(
        self,
        base_pv,
        minimum_values_per_reading=5,
        maximum_readings_per_frame=1_000,
        base_sample_rate=100_000,
        idle_acquire=True,
        idle_trigger_state=TetrammTrigger.FreeRun,
    ):
        self.range = epics_signal_rw(TetrammRange, base_pv + ":DRV:Range")
        self.sample_time = epics_signal_r(float, base_pv + ":DRV:SampleTime_RBV")

        self.values_per_reading = epics_signal_rw(
            int, base_pv + ":DRV:ValuesPerRead", base_pv + ":DRV:ValuesPerRead_RBV"
        )
        self.averaging_time = epics_signal_rw(
            float, base_pv + ":DRV:AveragingTime", base_pv + ":DRV:AveragingTime_RBV"
        )
        self.to_average = epics_signal_r(int, base_pv + ":DRV:NumAverage_RBV")
        self.averaged = epics_signal_r(int, base_pv + ":DRV:NumAveraged_RBV")

        self.acquire = epics_signal_rw(bool, base_pv + ":DRV:Acquire")

        self.overflows = epics_signal_r(int, base_pv + ":DRV:RingOverflows")

        self.channels = epics_signal_rw(TetrammChannels, base_pv + ":DRV:NumChannels")
        self.resolution = epics_signal_rw(
            TetrammResolution, base_pv + ":DRV:Resolution"
        )
        self.trigger = epics_signal_rw(TetrammTrigger, base_pv + ":DRV:TriggerMode")
        self.bias = epics_signal_rw(bool, base_pv + ":DRV:BiasState")
        self.bias_volts = epics_signal_rw(
            float, base_pv + ":DRV:BiasVoltage", base_pv + ":DRV:BiasVoltage_RBV"
        )

        self.geometry = epics_signal_rw(TetrammGeometry, base_pv + ":DRV:Geometry")

        self.base_sample_rate = base_sample_rate
        self.maximum_readings_per_frame = maximum_readings_per_frame
        self.minimum_values_per_reading = minimum_values_per_reading

        self.idle_acquire = idle_acquire
        self.idle_trigger_state = idle_trigger_state

    async def set_frame_time(self, seconds):
        await self.averaging_time.set(seconds / 1_000)
        values_per_reading = (
            seconds * self.base_sample_rate / self.maximum_readings_per_frame
        )
        if values_per_reading < self.minimum_values_per_reading:
            values_per_reading = self.minimum_values_per_reading
        await self.values_per_reading.set(values_per_reading)
        await self._refresh_file_size_dimensions(seconds)

    async def _refresh_file_size_dimensions(self, seconds):
        if not self.idle_acquire or self.idle_trigger_state != TetrammTrigger.FreeRun:
            self.acquire.set(False)
            self.trigger.set(TetrammTrigger.FreeRun)
            self.acquire.set(True)
            target = await self.to_average.get_value()
            await wait_for_value(self.averaged, target, seconds * 2)
            self.acquire.set(False)
