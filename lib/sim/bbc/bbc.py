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

# FUTURE devices (for full design) ...
# from sim.device.select_direct import Selector, Director
# from sim.device.orgate import PulseOr
from sim.device.arith import Counter
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
# ('p0_Next', 4.0),
# ('p1_AddressPm', 2.5),
# ('p2_PmFetchIr', 12.0),
# ('p3_PmFetchK_Clc', 20.0),
# ('p4_DmAddr', 10.0),
# ('p5_AddC_SaveA', 10.0),

pm_mnemonics = PulseRom(
    'pm_mnemonics',
    instruction_names)
pm_ir = PulseRom(
    'pm_ir',
    instruction_ir_bits)
pm_k = PulseRom(
    'pm_k',
    instruction_k_values)

count_pm_addr = Counter('pm_addr', n_bits=6)
# in: 'input'
# out: 'output', 'x_carry_out'

# Connect the 'next' signal : it needs to be converted to a '1' for a multibit counter input.
ir_plus_1 = SigSendCopy(name='ir+1')
ir_plus_1.input(0.0, Signal('_tmp', start_state=1))
ir_plus_1.connect('send', cycle.p0_Next)
# TODO: this signal will need to be OR-ed with k value (for jumps) and carry-out (for skips)
count_pm_addr.connect('input', ir_plus_1.output)

# Wire address and timing signals to all 3 PM roms
for pm in (pm_mnemonics, pm_ir, pm_k):
    pm.connect('addr', count_pm_addr.output)
    pm.connect('x_asel', cycle.p1_AddressPm)
    pm.connect('x_aclr', cycle.p5_AddC_SaveA)

pm_mnemonics.connect('x_read', cycle.p2_PmFetchIr)
pm_ir.connect('x_read', cycle.p2_PmFetchIr)
pm_k.connect('x_read', cycle.p3_PmFetchK_Clc)

# Split off top bit of instruction for immediate signal to preclear acc
ctrl_x_cla = sig_bitslice(pm_ir.out, 7, name='!cla')
# Rest goes to IR : these ones are all latched
ir_lower7 = sig_bitslice(pm_ir.out, 0, nbits=7)  # NB automatic naming
ir = PulseLatch('ir')
ir.connect('input', ir_lower7.output)

# Define individual, latched control signals by splitting off single IR bits.
for (num, (varname, signame)) in enumerate((
        ('ctrl_op_Ecy', 'Ecy'),
        ('ctrl_op_Eor', 'Eor'),
        ('ctrl_op_adc', 'adc'),
        ('ctrl_clc_c2a', 'clc_c2a'),
        ('ctrl_m2a_m2m_NOTa2m', 'm2a_m2m_~a2m'),
        ('ctrl_k2a_ATm', 'k2a_@m'),
        ('ctrl_k2m', 'k2m'))):
    locals()[varname] = sig_bitslice(ir.output, num, name=signame)

#
# acc = Accumulator('a', bits=8)
#
# cy = Counter('cy', bits=1)
# cy.cin.connect(acc.cout)
# cy.clr.connect(0) #clc

