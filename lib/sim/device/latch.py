import sys

sys.path.append(
    '/storage/emulated/0/qpython/')

from sim.signal import SIG_UNDEF
from sim.device import okeq, okin
from sim.device import Device, Action


class PulseLatch(Device):
    """
    A latching memory that catches
    any event on its input, resets
    with a 'clear' signal.

    """

    def __init__(self,
                 name,
                 t_data_2_clr=1,
                 t_clr_2_data=1,
                 t_out_delay=10,
                 *args, **kwargs):
        super(PulseLatch, self).__init__(
            name, *args, **kwargs)
        self._t_d2c = t_data_2_clr
        self._t_c2d = t_clr_2_data
        self._t_delay = t_out_delay
        self.add_output('output')
        self.reset()

    def reset(self):
        self._state = 'ready'

    @Device.input
    def input(self, time, signal):
        # assert self._state == 'ready'
        okeq(self._state, 'ready')
        if signal.state == 0:
            # Ignore, in this case
            return
        self._state = 'capturing'
        self.output.set(time, SIG_UNDEF)
        self.seq.addall([
            (time + self._t_delay,
             Action(self,
                    '_output_update',
                    signal.state)),
            (time + self._t_d2c,
             Action(self,
                    '_latched'))])

    @Device.input
    def clr(self, time, signal):
        okin(self._state,
             ['ready', 'set'])
        self._state = 'clearing'
        self.output.set(time, SIG_UNDEF)
        self.seq.addall([
            (time + self._t_delay,
             Action(self,
                    '_output_update',
                    state=0)),
            (time + self._t_c2d,
             Action(self,
                    '_cleared'))
        ])

    @Device.action
    def _latched(self, time):
        okeq(self._state, 'capturing')
        self._state = 'set'
        # now captured, wait for a clr signal

    @Device.action
    def _cleared(self, time):
        okeq(self._state, 'clearing')
        self._state = 'ready'

    @Device.action
    def _output_update(self, time, state):
        # Note: output updates after
        # a delay, quite separate from
        # internal state changes.
        self.output.set(time, state)
