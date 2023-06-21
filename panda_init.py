from bluesky import RunEngine

from bluesky.run_engine import call_in_bluesky_event_loop

from IPython import get_ipython

get_ipython().run_line_magic("autoawait", "call_in_bluesky_event_loop")

RE = RunEngine()

from p38 import panda#, panda_plans as ppl

pnd = panda.panda()


