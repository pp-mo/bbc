import sys

from sim.tests import \
    okeq, okin, setsig, fails

from sim.signal import Signal
from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.device.pulse_ram import PulseRam

ram = PulseRam('dm')
print(ram)

d_in = Signal('data')
addr = Signal('addr')
ard = Signal('!a_read')
aclr = Signal('!a_aclr')

ram.connect('d_in', d_in)
ram.connect('addr', addr)
ram.connect('x_read', ard)
ram.connect('x_aclr', aclr)

addr.trace()
d_in.trace()
ard.trace()
aclr.trace()
ram.out.trace()

print('\ncheck set, clr')
SEQ.addall([
    setsig(100.0, addr, 3),
    setsig(110.0, ard, '!'),
    setsig(112.0, aclr, '!'),
])
SEQ.run()
okeq(ram.out.state, 0)

print('\ncheck read, write')
SEQ.addall([
    setsig(100.0, addr, 2),
    setsig(110.0, ard, '!'),
    setsig(120.0, d_in, 213),
    setsig(122.0, aclr, '!'),
])
SEQ.run()
okeq(ram.out.state, 0)

print('\ncheck readback (without addr change)')
SEQ.addall([
    setsig(130.0, ard, '!'),
    setsig(132.0, aclr, '!'),
])
SEQ.run()
okeq(ram.out.state, 213)

print('\ncheck 0 on second read')
SEQ.addall([
    setsig(130.0, ard, '!'),
    setsig(132.0, aclr, '!'),
])
SEQ.run()
okeq(ram.out.state, 0)

print('\nwrite values to 2 different locations + read back + check 0 after')
SEQ.addall([
    setsig(200.0, addr, 11),
    setsig(202.0, ard, '!'),
    setsig(204.0, d_in, 111),
    setsig(206.0, aclr, '!'),
    setsig(220.0, addr, 22),
    setsig(222.0, ard, '!'),
    setsig(224.0, d_in, 222),
    setsig(226.0, aclr, '!'),

    setsig(240.0, addr, 11),
    setsig(242.0, ard, '!'),
    setsig(244.0, aclr, '!'),

    setsig(260.0, addr, 22),
    setsig(262.0, ard, '!'),
    setsig(264.0, aclr, '!'),

    setsig(280.0, addr, 11),
    setsig(282.0, ard, '!'),
    setsig(284.0, aclr, '!'),
])
SEQ.run(255.)
okeq(ram.out.state, 111)
SEQ.run(275.)
okeq(ram.out.state, 222)
SEQ.run()
okeq(ram.out.state, 0)


