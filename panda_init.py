from pathlib import Path
from typing import Dict, Iterator

import tables
from bluesky import plan_stubs as bps
from bluesky import plans as bp
from bluesky import preprocessors as bpp
from bluesky import Msg, RunEngine
from bluesky.protocols import Descriptor, Flyable, PartialEvent, Readable
from bluesky.run_engine import call_in_bluesky_event_loop
from ophyd.v2.core import AsyncStatus, DeviceCollector, wait_for_value
from ophyd_epics_devices.areadetector import (
    ADDriver,
    HDFStreamerDet,
    NDFileHDF,
    TmpDirectoryProvider,
)
from ophyd_epics_devices.panda import PandA


class FlyingPanda(Flyable):
    def __init__(self, panda):
        self.dev = panda
        self._frames = []

    @property
    def name(self) -> str:
        return self.dev.name

    async def set_frames(self, frames):
        table = tables.build_table(*zip(*frames))
        await self.dev.seq1.tables.set(table)

    @AsyncStatus.wrap
    async def kickoff(self) -> None:
        await self.dev.seq1.enable.set("ONE")
        await wait_for_value(self.dev.seq1.active, "1", 5)

    @AsyncStatus.wrap
    async def complete(self) -> None:
        await wait_for_value(self.dev.seq1.active, "0", 20)
        await self.dev.seq1.enable.set("ZERO")

    def collect(self) -> Iterator[PartialEvent]:
        yield from iter([])

    def describe_collect(self) -> Dict[str, Dict[str, Descriptor]]:
        return {}


@bpp.run_decorator()
def collect_n(det: HDFStreamerDet, panda: FlyingPanda, frames: int, tpf: int, expo: float):
    yield from bps.mov(det.drv.acquire_time, expo, det.drv.num_images, frames)

    row = tables.frame(time1=tpf - 10, time2=10, outa2=1, repeats=frames)
    yield from bps.mov(panda.dev.seq1.table, tables.build_table(*zip(*[row])))

    yield Msg("stage", det)

    yield from bps.kickoff(det, wait=False, group="kick")
    yield from bps.kickoff(panda, wait=False, group="kick")

    yield from bps.wait(group="kick")

    det_stat = yield from bps.complete(det, wait=False, group="complete")
    panda_state = yield from bps.complete(panda, wait=False, group="complete")

    while det_stat and not det_stat.done:
        yield from bps.sleep(1)
        yield from bps.collect(det, stream=True, return_payload=False)
    yield from bps.wait(group="complete")

    yield Msg("unstage", det)


RE = RunEngine()

d11_dir = TmpDirectoryProvider()
d11_dir._directory = Path("/dls/tmp/qan22331/panda_ad")

with DeviceCollector():
    pnd = PandA("BL38P-PANDA")
    d11_drv = ADDriver("BL38P-DI-DCAM-03:DET:")
    d11_hdf = NDFileHDF("BL38P-DI-DCAM-03:HDF5:")
    d11 = HDFStreamerDet(d11_drv, d11_hdf, d11_dir)

fp = FlyingPanda(pnd)

RE(collect_n(d11, fp, 8, 1200, 0.2))
