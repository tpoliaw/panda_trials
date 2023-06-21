# PandA trials

## Required setup

### Panda IOC

### Python environment
Needs 
* ophyd-epics-devices
 * From https://github.com/bluesky/ophyd-epics-devices (panda-ideas-testing branch)
* ophyd
* p4p
* ipython
 * Shouldn't be tied to a specific repl but things didn't work well from others.
* bluesky
 * Not really needed but it sets up some ipython stuff that may or may not be
   useful.

### Starting demo

```python
$ ipython -i panda_init.py
>>> import tables
>>> tables.display("helloWorld")
```

Assumes the panda IOC is running with a PV of `TS-PANDA`.

## tables.py

Currently the main module of functions used for testing the panda.
Individual rows of a sequencer table can be built using the `frame` method that 
creates a `Frame` object using default values for all non-specified options.

NB dataclasses/pydantic models are not as usable as namedtuples as being iterable
means tuples can be inverted to converted from row-wise to column-wise form more
easily.

A list (or any other iterable) of frames can be passed to the `build_table` function
to create a `SeqTable` that can be passed to the `seq1.table` panda block.

### display function

Demo function for displaying scrolling text on the spinning light demo. This
relies on the double buffered sequence table in new versions of the panda firmware
to continuously update the table to display scrolling text.
