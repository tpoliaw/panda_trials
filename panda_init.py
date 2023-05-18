from bluesky import RunEngine

from bluesky.run_engine import call_in_bluesky_event_loop

from IPython import get_ipython

get_ipython().run_line_magic("autoawait", "call_in_bluesky_event_loop")

RE = RunEngine()

from ophyd_epics_devices.panda import PandA
from ophyd.v2.core import DeviceCollector
from ophyd_epics_devices.panda import PandA, SeqTable, SeqTrigger

with DeviceCollector():
    my_panda = PandA("TS-PANDA")


from collections import namedtuple
import bluesky.plan_stubs as bps
import numpy as np

from pyfiglet import Figlet

Frame = namedtuple('Frame', ("repeats", "trigger", "position", "time1", "outa1", "outb1", "outc1", "outd1", "oute1", "outf1", "time2", "outa2", "outb2", "outc2", "outd2", "oute2", "outf2"))

def frame(*, repeats=1, trigger="Immediate", position=0, time1=0, outa1=0, outb1=0, outc1=0, outd1=0, oute1=0, outf1=0, time2=0, outa2=0, outb2=0, outc2=0, outd2=0, oute2=0, outf2=0):
    return Frame(repeats, trigger, position, time1, outa1, outb1, outc1, outd1, oute1, outf1, time2, outa2, outb2, outc2, outd2, oute2, outf2)

def render(txt, font='clr6x6', width=200):
    f = Figlet(font=font, width=width)
    lines = f.renderText(txt).splitlines()
    return [[0 if c == ' ' else 1 for c in line] for line in lines]

def configure_text(pnd, txt, font="clr6x6", start=600, step=8):
    text_frames = zip(*render(txt, font, width=start//step)[::-1])
    posn = start
    frames = []
    frames.append(frame(trigger="POSA>=POSITION", position=posn))
    for (a, b, c, d, e, f, *_) in text_frames:  # type: ignore mypy can't count to 6
        frames.append(frame(trigger="POSA<=POSITION", position=posn, outa2=a, outb2=b, outc2=c, outd2=d, oute2=e, outf2=f))
        posn -= step
    yield from panda_frames(pnd, frames)


def table_from_frames(frames):
    return build_table(*zip(*frames))

def panda_frames(pnd, frames):
    table = build_table(*zip(*frames))
    yield from panda_config(pnd, table)

def build_table(repeats, trigger, position, time1, outa1, outb1, outc1, outd1, oute1, outf1, time2, outa2, outb2, outc2, outd2, oute2, outf2):
    table = SeqTable()
    table['REPEATS'] = np.array(repeats, dtype=np.uint16)
    table['POSITION'] = np.array(position, dtype=np.int32)
    table['TRIGGER'] = np.array(trigger)
    table['TIME1'] = np.array(time1, np.uint32)
    table['OUTA1'] = np.array(outa1, np.uint8)
    table['OUTB1'] = np.array(outb1, np.uint8)
    table['OUTC1'] = np.array(outc1, np.uint8)
    table['OUTD1'] = np.array(outd1, np.uint8)
    table['OUTE1'] = np.array(oute1, np.uint8)
    table['OUTF1'] = np.array(outf1, np.uint8)
    table['TIME2'] = np.array(time2, np.uint32)
    table['OUTA2'] = np.array(outa2, np.uint8)
    table['OUTB2'] = np.array(outb2, np.uint8)
    table['OUTC2'] = np.array(outc2, np.uint8)
    table['OUTD2'] = np.array(outd2, np.uint8)
    table['OUTE2'] = np.array(oute2, np.uint8)
    table['OUTF2'] = np.array(outf2, np.uint8)
    return table

def panda_config(pnd, table):
    yield from bps.mov(pnd.seq1.table, table)

