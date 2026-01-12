import sys

sys.path.append(
    '/storage/emulated/0/qpython/')

from sim.signal import Signal, SIG_UNDEF
from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.device.latch import PulseLatch

from sim.tests import okeq, okin, setsig, fails

latch = PulseLatch(
    'latch',
    t_data_2_clr=2.0,
    t_clr_2_data=2.0,
    t_out_delay=5.)

din = Signal('d_in')
clr = Signal('clr')
latch.connect('input', din)
latch.connect('clr', clr)

din.trace()
clr.trace()
latch.output.trace()

print('\ncheck set, clr, set')
SEQ.addall([
    setsig(100.0, din, 77),
    setsig(200.0, clr, '!'),
    setsig(250.0, din, 35),
])
SEQ.run(10)
okeq(latch.output.state, 0)
SEQ.run(100.1)
okeq(latch.output.state, SIG_UNDEF)
SEQ.run(105.1)
okeq(latch.output.state, 77)
SEQ.run(200.1)
okeq(latch.output.state, SIG_UNDEF)
SEQ.run(204.9)
okeq(latch.output.state, SIG_UNDEF)
SEQ.run(205.1)
okeq(latch.output.state, 0)
SEQ.run(255.1)
okeq(latch.output.state, 35)

print('\ncheck clr twice')
SEQ.clear()
latch.reset()
SEQ.addall([
    setsig(300.0, clr, '!'),
    setsig(320.0, clr, '!'),
])
SEQ.run()

print('\ncheck set twice fails.')
SEQ.clear()
latch.reset()
SEQ.addall([
    setsig(400.0, clr, '!'),
    setsig(410.0, din, 35),
    setsig(420.0, din, 35),
])
with fails():
    SEQ.run()

print('\ncheck 0 ok before set, not after.')
SEQ.clear()
latch.reset()
SEQ.addall([
    setsig(500.0, clr, '!'),
    setsig(520.0, din, 0),
    setsig(530.0, din, 35),
    setsig(540.0, din, 0),
])
with fails():
    SEQ.run()

print('\ncheck data too soon after clr')
SEQ.clear()
latch.reset()
SEQ.addall([
    setsig(600.0, clr, '!'),
    setsig(601.0, din, 35),
])
with fails():
    SEQ.run()

print('\ncheck clr too soon after clr')
SEQ.clear()
latch.reset()
SEQ.addall([
    setsig(600.0, clr, '!'),
    setsig(601.0, clr, '!'),
])
with fails():
    SEQ.run()

print('\ncheck clr too soon after data')
SEQ.clear()
latch.reset()
SEQ.addall([
    setsig(700.0, clr, '!'),
    setsig(710.0, din, 54),
    setsig(711.0, clr, '!'),
])
with fails():
    SEQ.run()
