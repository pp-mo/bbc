from sim.signal import Signal, SIG_UNDEF
from sim.sequencer import DEFAULT_SEQUENCER as SEQ

from sim.tests import okeq, okin, setsig, fails

from sim.device.arith import Counter


counter = Counter(
    'count', n_bits=4,
    onebit_kwargs={
        't_toggle_0_to_1': 3.,
        't_toggle_1_to_0': 3.,
        't_out_2_carry': 1.,
        't_clear_2_carry': 2.,
        't_clear_onoff': 4.,
        't_eor_onoff': 2.})

din = Signal('d_in')
clr = Signal('clr')
counter.connect('input', din)
counter.connect('clear', clr)

din.trace()
clr.trace()
counter.output.trace()
counter.x_carry_out.trace()

# for bit_counter in counter._bit_counters:
#     bit_counter.output.trace()
#     bit_counter.x_carry_out.trace()
#
# for carry_gate in counter._carry_gates:
#     carry_gate.output.trace()

    
SEQ.addall([
    setsig(100.0, din, 1),
    setsig(120.0, din, 1),
    setsig(140.0, din, 1),
    setsig(200.0, clr, 1),
    setsig(210.0, clr, 0),
    setsig(300.0, din, 1),
])
SEQ.run()

