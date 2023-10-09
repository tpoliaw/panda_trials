from time import time
from enum import Enum
from ophyd.v2.core import Device, StandardReadable, wait_for_value
from ophyd.v2.epics import epics_signal_r, epics_signal_rw


class TetrammRange(Enum):
    uA = "+- 120 uA"
    nA = "+- 120 nA"


class TetrammTrigger(Enum):
    FreeRun = "Free run"
    ExtTrigger = "Ext. trig."
    ExtBulb = "Ext. bulb"
    ExtGate = "Ext. gate"


class TetrammChannels(Enum):
    One = "1"
    Two = "2"
    Four = "4"


class TetrammResolution(Enum):
    SixteenBits = "16 bits"
    TwentyFourBits = "24 bits"

    def __repr__(self):
        match self:
            case TetrammResolution.SixteenBits:
                return "16bits"
            case TetrammResolution.TwentyFourBits:
                return "24bits"


class TetrammGeometry(Enum):
    Diamond = "Diamond"
    Square = "Square"


class Tetramm(StandardReadable):
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

    idle_averaging_time: float
    """Time that readings should be averaged over then no collection is running"""

    idle_values_per_reading: int
    """The number of values that should be averaged to give each sample when no collection is running"""

    collection_resolution: TetrammResolution = TetrammResolution.TwentyFourBits
    """Default resolution to be used for collections"""

    collection_geometry: TetrammGeometry = TetrammGeometry.Square
    """Default geometry to be used for collections"""

    collection_range: TetrammRange = TetrammRange.uA
    """Default range to be used for collections"""

    def __init__(
        self,
        name,
        base_pv,
        minimum_values_per_reading=5,
        maximum_readings_per_frame=1_000,
        base_sample_rate=100_000,
        idle_acquire=True,
        idle_trigger_state=TetrammTrigger.FreeRun,
        idle_averaging_time=0.1,
        idle_values_per_reading=10,
    ):
        self._base_pv = base_pv
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

        self.current_1 = epics_signal_r(float, base_pv + ":Cur1:MeanValue_RBV")
        self.current_2 = epics_signal_r(float, base_pv + ":Cur2:MeanValue_RBV")
        self.current_3 = epics_signal_r(float, base_pv + ":Cur3:MeanValue_RBV")
        self.current_4 = epics_signal_r(float, base_pv + ":Cur4:MeanValue_RBV")

        self.position_x = epics_signal_r(float, base_pv + ":PosX:MeanValue_RBV")
        self.position_y = epics_signal_r(float, base_pv + ":PosY:MeanValue_RBV")

        self.base_sample_rate = base_sample_rate
        self.maximum_readings_per_frame = maximum_readings_per_frame
        self.minimum_values_per_reading = minimum_values_per_reading

        self.idle_acquire = idle_acquire
        self.idle_trigger_state = idle_trigger_state
        self.idle_averaging_time = idle_averaging_time
        self.idle_values_per_reading = idle_values_per_reading

        self.set_readable_signals(
            read=[
                self.current_1,
                self.current_2,
                self.current_3,
                self.current_4,
                self.position_x,
                self.position_y,
            ],
            config=[self.values_per_reading, self.averaging_time, self.sample_time],
        )
        super().__init__(name=name)

    def describe(self):
        return {
            "current_1": {
                "source": self.current_1.source,
                "dtype": "number",
                "shape": [],
            },
            "current_2": {
                "source": self.current_1.source,
                "dtype": "number",
                "shape": [],
            },
            "current_3": {
                "source": self.current_1.source,
                "dtype": "number",
                "shape": [],
            },
            "current_4": {
                "source": self.current_1.source,
                "dtype": "number",
                "shape": [],
            },
            "position_x": {
                "source": self.current_1.source,
                "dtype": "number",
                "shape": [],
            },
            "position_y": {
                "source": self.current_1.source,
                "dtype": "number",
                "shape": [],
            },
        }

    def read(self):
        return {
                'current_1': {'value': self.current_1.get_value(), 'timestamp': time()},
                'current_2': {'value': self.current_2.get_value(), 'timestamp': time()},
                'current_3': {'value': self.current_3.get_value(), 'timestamp': time()},
                'current_4': {'value': self.current_4.get_value(), 'timestamp': time()},
                'position_x': {'value': self.position_x.get_value(), 'timestamp': time()},
                'position_y': {'value': self.position_y.get_value(), 'timestamp': time()},
                }

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

    def stage(self):
        # set averaging time
        # set dimensions
        # stop idle acquire
        # set trigger to ext trig
        # set collection time?
        # set geometry
        # set range
        # set resolution
        # set acquire?
        # set recording?
        pass

    def unstage(self):
        # stop acquiring
        # set idle trigger state
        # set idle averaging time
        # set idle values per reading
        # set acquire if needed
        pass
