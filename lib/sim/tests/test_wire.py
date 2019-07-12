import sys

path = '/storage/emulated/0/qpython/'
if path not in sys.path:
    sys.path.append(path)

import sim.tests
from sim.signal import Signal, SIG_UNDEF
from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.device import Device, Action, ClockTick
from sim.device.wire import Wire
from sim.device import okeq, okin


# Test-only (?) xor gate
class Xor2(Device):
    def __init__(self, name,
                 settle=2.5,
                 *args, **kwargs):
        super(Xor2, self).__init__(
            name, *args, **kwargs)
        self._settle = settle
        self._in = [0, 0]
        self._changes = [0, 0]
        self.add_output('out', SIG_UNDEF)

    @Device.input
    def in1(self, t, sig):
        self._in[0] = sig.state
        self._changes[0] = 1
        self.out.set(t, SIG_UNDEF)
        self.seq.add((
            t + self._settle,
            Action(self, '_done', 0)))

    @Device.input
    def in2(self, t, sig):
        self._in[1] = sig.state
        self._changes[1] = 1
        self.out.set(t, SIG_UNDEF)
        self.seq.add((
            t + self._settle,
            Action(self, '_done', 1)))

    @Device.action
    def _done(self, t, i_in):
        self._changes[i_in] = 0
        if not any(self._changes):
            v1, v2 = self._in
            self.out.set(
                t, v1 ^ v2)


sig1 = Signal('s01')
w01 = Wire('w01', delay=20.)
print w01
w01.connect('input', sig1)

x01 = Xor2('xor01')
x01.trace('_done')
x01.connect('in1', sig1)
x01.connect('in2', w01.output)

SEQ.add((0.,
         lambda t: sig1.set(t, 0)))
SEQ.run()
okeq(sig1.state, 0)
print('remaining events:')
print(SEQ.events)
print('')

sig1.trace()
w01.output.trace()
x01.out.trace()

SEQ.add((100.,
         lambda t: sig1.set(t, 1)))
SEQ.add((200.,
         lambda t: sig1.set(t, 0)))
SEQ.add((300.,
         lambda t: sig1.set(t, 1)))

print('\nrun to 100.1')
SEQ.run(100.1)
print('check sig=1, wire=0, xor=x')
okeq(sig1.state, 1)
okeq(w01.output.state, 0)
okeq(x01.out.state, SIG_UNDEF)

print('\n run to 102.6')
SEQ.run(102.6)
print('check sig=1, wire=0, xor=1')
okeq(sig1.state, 1)
okeq(w01.output.state, 0)
okeq(x01.out.state, 1)

print('\n run to 120.1')
SEQ.run(120.1)
print('check sig=1, wire=1, xor=x')
okeq(sig1.state, 1)
okeq(w01.output.state, 1)
okeq(x01.out.state, SIG_UNDEF)

print('\n run to 122.6')
SEQ.run(122.6)
print('check sig=1, wire=1, xor=0')
okeq(sig1.state, 1)
okeq(w01.output.state, 1)
okeq(x01.out.state, 0)
