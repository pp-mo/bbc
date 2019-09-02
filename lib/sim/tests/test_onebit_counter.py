from sim.signal import Signal, SIG_UNDEF
from sim.sequencer import DEFAULT_SEQUENCER as SEQ

from sim.tests import okeq, okin, setsig, fails

from sim.device.arith import CounterOnebit


counter = CounterOnebit(
    'c1b',
     t_toggle_0_to_1=3.,
     t_toggle_1_to_0=3.,
     t_out_2_carry=1.,
     t_clear_2_carry=2.,
     t_clear_onoff=4.,
     t_eor_onoff=2.)

din = Signal('d_in')
clr = Signal('clr')
ore = Signal('ore')
counter.connect('input', din)
counter.connect('clear', clr)
counter.connect('enable_or', ore)

din.trace()
clr.trace()
counter.output.trace()
counter.x_carry_out.trace()

SEQ.addall([
    setsig(100.0, din, 1),
    setsig(110.0, din, 1),
    setsig(120.0, din, 1),
    setsig(150.0, clr, 1),
    setsig(160.0, clr, 0),
    setsig(180.0, clr, 1),
    setsig(181.0, ore, 1),
    setsig(190.0, clr, 0),
    setsig(200.0, din, 1),
    setsig(210.0, din, 1),
    setsig(220.0, din, 1),
    setsig(223.0, clr, 0),
])
SEQ.run()

SEQ.addall([
    setsig(250.0, clr, 1),
    setsig(251.0, clr, 0)
])
with fails(ValueError):
    SEQ.run()
