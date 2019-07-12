# Ball Bearing Computer simulation

import sys

sys.path.append(
    '/storage/emulated/0/qpython/')

from sim.signal import Signal
from sim.sequencer import DEFAULT_SEQUENCER as SEQ

from sim.device.wire import Wire
from sim.device.pulse_rom import PulseRom
from sim.device.pulse_ram import PulseRam
from sim.device.latch import PulseLatch
from sim.device.select_direct import Selector, Director
from sim.device.orgate import PulseOr
from sim.device.arith import Accumulator, Counter
from sim.device.pseudo_devices import \
    sig_join, sig_bitslice, SigSendCopy
        # NOTE: sender produces a triggered event from a state output
        # in ball-bearing terms, this is a COPY : needed for ACC and CY copying.
        # By contrast, we allow PM and DM addresses to be state-driven (from
        # pm_addr and m_addr), assuming that there is a specific mechanism for
        # this ...

from sim.bbc.code import code

instruction_names = [
    instr[0] for instr in code]
instruction_ir_bits = [
    instr[1] for instr in code]
instruction_k_values = [
    (instr[2]
     if len(instr) > 2
     else 0)
    for instr in code]

from sim.bbc.controller import BbcController

cycle = BbcController('bbc')

pm_mnemonics = PulseRom(
    'pm_mnemonics',
    instruction_names)
pm_ir = PulseRom(
    'pm_ir',
    instruction_ir_bits)
pm_k = PulseRom(
    'pm_k',
    instruction_k_values)

ir = PulseLatch('ir')


acc = Accumulator('a', bits=8)

cy = Counter('cy', bits=1)
cy.cin.connect(acc.cout)
cy.clr.connect(0) #clc

count_pm_addr = Counter('pm_addr', bits=6)
count_pm_addr.din.connect()