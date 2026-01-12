from sim.signal import Signal, SIG_UNDEF
from sim.sequencer import DEFAULT_SEQUENCER as SEQ

from sim.tests import okeq, okin, setsig, fails

from sim.device.arith import Counter


counter = Counter(
    'TstCount1', n_bits=2,
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
    setsig(160.0, din, 1),
])

COUNTER_CARRYOUTS_COUNT = 0

def carry_out_callback(time, signal):
    global COUNTER_CARRYOUTS_COUNT
    COUNTER_CARRYOUTS_COUNT += 1

counter.x_carry_out.add_connection(carry_out_callback)

okeq(counter.output.state, 0)
okeq(COUNTER_CARRYOUTS_COUNT, 0)

SEQ.run(101.)
okeq(counter.output.state, SIG_UNDEF)
okeq(COUNTER_CARRYOUTS_COUNT, 0)

SEQ.run(119.)
okeq(counter.output.state, 1)
okeq(COUNTER_CARRYOUTS_COUNT, 0)

SEQ.run(121.)
okeq(counter.output.state, SIG_UNDEF)
okeq(COUNTER_CARRYOUTS_COUNT, 0)

SEQ.run(139.)
okeq(counter.output.state, 2)
okeq(COUNTER_CARRYOUTS_COUNT, 0)

SEQ.run(159.)
okeq(counter.output.state, 3)
okeq(COUNTER_CARRYOUTS_COUNT, 0)

SEQ.run(179.)
okeq(counter.output.state, 0)
okeq(COUNTER_CARRYOUTS_COUNT, 1)  # After 4 counts, finally get a carry

# Reset carries-count, just for clarity of testing
COUNTER_CARRYOUTS_COUNT = 0

# Add two multi-bit values to check arithmetic
SEQ.addall([
    setsig(250.0, din, 2),
    setsig(270.0, din, 3),
])
SEQ.run(280.)
okeq(counter.output.state, 1)
okeq(COUNTER_CARRYOUTS_COUNT, 1)


# Reset carries-count, just for clarity of testing
COUNTER_CARRYOUTS_COUNT = 0

# Start a clearing period
SEQ.addall([
    setsig(300.0, clr, 1),
])
SEQ.run(301.)
okeq(counter.output.state, SIG_UNDEF)  # in the clearing process

# After a settling, should all be empty.
SEQ.run(319.)
okeq(counter.output.state, 0)
okeq(COUNTER_CARRYOUTS_COUNT, 0)

# Add an input while in clear : should have no (ultimate) effect.
SEQ.addall([
    setsig(350.0, din, 1),
])
SEQ.run(351.)
okeq(counter.output.state, SIG_UNDEF)  # output state is temporarily unstable.
SEQ.run(369.)
okeq(counter.output.state, 0)  # Output returns to 0 in the end
okeq(COUNTER_CARRYOUTS_COUNT, 0)

# Release clear + add 2 more inputs.
SEQ.addall([
    setsig(400.0, clr, 0),
    setsig(420.0, din, 3),
    setsig(440.0, din, 2),
])
SEQ.run()
okeq(counter.output.state, 1)
okeq(COUNTER_CARRYOUTS_COUNT, 1)
