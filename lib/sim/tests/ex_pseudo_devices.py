import sys

sys.path.append(
    '/storage/emulated/0/qpython/')

from sim.signal import Signal, SIG_UNDEF
from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.device.pseudo_devices import \
    SigBitslice, SigJoin, sig_bitslice, sig_join

from sim.tests import okeq, okin, setsig, fails

sig_a = Signal('a')
d_a0 = sig_bitslice(sig_a, 0)
d_a2 = sig_bitslice(sig_a, 2, name='a2_x')
d_a12 = sig_bitslice(sig_a, 1, nbits=2)
okeq(d_a0.name, 'a:0')
okeq(d_a2.name, 'a2_x')
okeq(d_a12.name, 'a:1..2')
a0 = d_a0.output
a2 = d_a2.output
a12 = d_a12.output
okeq(a0.name, 'a:0.output')
okeq(a2.name, 'a2_x.output')
okeq(a12.name, 'a:1..2.output')

print('\ncheck bit slices')
SEQ.addall([
    setsig(100.0, sig_a, 0b0101),
    setsig(200.0, sig_a, SIG_UNDEF),
    setsig(300.0, sig_a, 0b0010),
])
SEQ.run(10.)
okeq(a0.state, 0)
okeq(a2.state, 0)
okeq(a12.state, 0)

SEQ.run(100.)
okeq(a0.state, 1)
okeq(a2.state, 1)
okeq(a12.state, 0b10)

SEQ.run(200.)
okeq(a0.state, SIG_UNDEF)
okeq(a2.state, SIG_UNDEF)
okeq(a12.state, SIG_UNDEF)

SEQ.run()
okeq(a0.state, 0)
okeq(a2.state, 0)
okeq(a12.state, 0b01)
print('')

print('check slice chaining')
a12_1 = sig_bitslice(a12, 1).output
okeq(a12_1.name,
     'a:1..2.output:1.output')

sig_a.set(0., 0b0100)
okeq(a12_1.state, 1)
sig_a.set(0., 0b11011)
okeq(a12_1.state, 0)

sig_a.set(0., 0)
sig_b = Signal('b')
sig_c = Signal('c')
print('\ncheck joined signals: one change')
d_joined = sig_join(
    'join',
    [
        (sig_a, 2),
        (sig_b, 1),
        (sig_c, 2),
    ])

joined = d_joined.output

events = []


def out_ev(time, signal):
    global events
    events.append(
        (time, signal.state))


joined.add_connection(out_ev)
# sig_a.add_connection(out_ev)

SEQ.addall([
    setsig(100.0, sig_a, 0b0101),
    # abc= 01/0/00
])
events = []
SEQ.run(10.)
okeq(events, [])

sig_a.trace()
sig_b.trace()
sig_c.trace()
d_joined.trace('in_1')
d_joined.trace('in_2')
d_joined.trace('in_3')
d_joined.trace('_update_output')
joined.trace()

events = []
SEQ.run(100.)
okeq(events,
     [
         (100., 0b01000),
     ])

print('\ncheck joined signals: -> invalid')
SEQ.addall([
    setsig(200.0, sig_b, SIG_UNDEF),
])
events = []
SEQ.run(200.)
okeq(events,
     [
         # abc= 01/0/00
         (200., SIG_UNDEF),
         # abc= 01/X/00
     ])

print('\ncheck joined signals: -> valid')
SEQ.addall([
    # abc= 01/X/00
    setsig(210.0, sig_b, 1),
    # abc= 01/1/00
])
events = []
SEQ.run(210.)
okeq(events,
     [
         (210., 0b01100),
     ])

print('\ncheck joined signals: combined changes')
SEQ.addall([
    # abc= 01/1/00
    setsig(300.0, sig_b, 0),
    setsig(300.0, sig_a, 0b111),
    setsig(300.0, sig_c, 0b11),
    # abc= 11/0/11
])
events = []
SEQ.run(300.)
okeq(events,
     [
         (300., 0b11011),
     ])

print('')
print('check all-events operation')
SEQ.addall([
    # abc= 11/0/11
    setsig(400.0, sig_b, 1),
    # abc= 11/1/11
    setsig(400.0, sig_a, 0b10),
    # abc= 10/1/11
    setsig(400.0, sig_c, 0b1101),
    # abc= 10/1/01
])
d_joined.pass_all_events = True
events = []
SEQ.run(400.)
okeq(events,
     [
         (400., 0b11111),
         (400., 0b10111),
         (400., 0b10101),
     ])
