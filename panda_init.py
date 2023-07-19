from pathlib import Path
import tables
from bluesky import RunEngine, Msg
from bluesky.protocols import Flyable, Readable, PartialEvent, Descriptor
from bluesky.run_engine import call_in_bluesky_event_loop
from bluesky import plans as bp, plan_stubs as bps, preprocessors as bpp
# from IPython import get_ipython

from ophyd.v2.core import DeviceCollector, AsyncStatus, wait_for_value
from ophyd_epics_devices.panda import PandA
from ophyd_epics_devices.areadetector import ADDriver, NDFileHDF, HDFStreamerDet, TmpDirectoryProvider

from typing import Iterator, Dict

# get_ipython().run_line_magic("autoawait", "call_in_bluesky_event_loop")


class FlyingPanda(Flyable):
    def __init__(self, panda):
        self.dev = panda
        self._start_status = None
        self._frames = []
    @property
    def name(self) -> str:
        return "panda"
    async def set_frames(self, frames):
        table = tables.build_table(*zip(*frames))
        return self.dev.seq1.tables.set(table)
    @AsyncStatus.wrap
    async def kickoff(self) -> None:
        await self.dev.seq1.enable.set('ONE')
    @AsyncStatus.wrap
    async def complete(self) -> None:
        await wait_for_value(self.dev.seq1.active, "1", 20)
        await wait_for_value(self.dev.seq1.active, "0", 20)
        await self.dev.seq1.enable.set('ZERO')
    def collect(self) -> Iterator[PartialEvent]:
        yield from iter([])
    def describe_collect(self) -> Dict[str, Dict[str, Descriptor]]:
        return {}

@bpp.run_decorator()
def collect_n(det, panda, frames, tpf, expo):
    yield from bps.mov(det.drv.acquire_time, expo, det.drv.num_images, frames)

    row = tables.frame(time1=tpf-10, time2=10, outa2=1, repeats=frames)
    yield from bps.mov(panda.dev.seq1.table, tables.build_table(*zip(*[row])))

    result = yield Msg('stage', det)
    yield from bps.wait(result)

    yield from bps.kickoff(det, wait=False, group="kick")
    yield from bps.kickoff(panda, wait=False, group="kick")

    yield from bps.wait(group="kick")

    det_stat = yield from bps.complete(det, wait=False, group="complete")
    panda_state = yield from bps.complete(panda, wait=False, group="complete")
    # yield from bps.sleep(3)

    while det_stat and not det_stat.done:
        yield from bps.sleep(1)
        yield from bps.collect(det, stream=True, return_payload=False)
    yield from bps.wait(group="complete")

    yield Msg('unstage', det)




RE = RunEngine()

d11_dir = TmpDirectoryProvider()
d11_dir._directory = Path('/dls/tmp/qan22331/panda_ad')

with DeviceCollector():
    pnd = PandA("BL38P-PANDA")
    d11_drv = ADDriver("BL38P-DI-DCAM-03:DET:")
    d11_hdf = NDFileHDF("BL38P-DI-DCAM-03:HDF5:")
    d11 = HDFStreamerDet(d11_drv, d11_hdf, d11_dir)

fp = FlyingPanda(pnd)

try:
    RE(collect_n(d11, fp, 8, 1200, 0.2))
except Exception as e:
    print(e)
    
