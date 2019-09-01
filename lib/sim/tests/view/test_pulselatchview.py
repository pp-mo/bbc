import six.moves

from sim.signal import Signal, SIG_UNDEF
from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.device.latch import PulseLatch

from sim.tests import okeq, okin, setsig, fails

def runtest():
    latch = PulseLatch(
        'latch',
        t_data_2_clr=5.0,
        t_clr_2_data=5.0,
        t_out_delay=2.)

    din = Signal('d_in')
    clr = Signal('clr')
    latch.connect('input', din)
    latch.connect('clr', clr)

    din.trace()
    clr.trace()
    latch.output.trace()

    print('\ncheck set, clr, set')
    SEQ.addall([
        setsig(5.0, din, 77),
        setsig(20.0, clr, '!'),
        setsig(40.0, din, 35),
    ])


    from sim.view import device_view, viz

    import matplotlib.pyplot as plt

    latchview = device_view(latch,
        input_xy=(0, 10),
        output_xy=(0, 2),
        value_text_kwargs={'fontsize':60})

    scene = [latchview]
    ax = viz(scene, until_seqtime=350.0,
             speedup_factor=10.0, frame_interval_secs=0.05,
             pause_in_gaps=True)

    print('\n\nRETURN TO EXIT...>')
    six.moves.input()


if __name__ == '__main__':
    runtest()
