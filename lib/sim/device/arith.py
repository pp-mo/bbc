# Accumulator and adder arithmetic

from sim.signal import SIG_UNDEF
from sim.device import okeq, okin
from sim.device import Device, Action


class AdderOnebit(Device):
    """
    A one-bit store with increment-toggle, carry-out and async clear.

    """

    def __init__(self,
                 name,
                 t_toggle_0_to_1=2,
                 t_toggle_1_to_0=2,
                 t_out_delay=6,
                 t_carry_delay=6,
                 *args, **kwargs):
        super(PulseLatch, self).__init__(
            name, *args, **kwargs)
        self._t_0_1 = t_toggle_0_to_1
        self._t_1_0 = t_toggle_1_to_0
        self._t_delay = t_out_delay
        self._t_carry = t_carry_delay
        self.add_output('output', start_value=0)
        self.add_output('x_carry_out')
        self.reset()

    def reset(self):
        self._state = 'ready'
        self._value = 0

    @Device.input
    def input(self, time, signal):
        # assert self._state == 'ready'
        okeq(self._state, 'ready')
        if signal.state == 0:
            # Ignore, in this case
            return
        self._state = 'toggling'
        self._value = 1 - self._value
        self.output.set(time, SIG_UNDEF)
        toggle_delay = [self._t_0_1, self._t_1_0][self._value]
        acts = [
            (time + toggle_delay,
             Action(self,
                    '_update_output', self._value))]
        if self._value == 0:
            acts += [
                (time + self._t_carry,
                 Action(self, '_carry_out'))]
        self.seq.addall(acts)

    @Device.action
    def _update_output(self, time):
        okeq(self.state, 'toggling')
        self._state = 'ready'
        self.output.set(time, self._state)

    def _carry_out(self, time):
        okeq(self.state, 'toggling')
        self.output.set(time, self._value)
        self.state = 'ready'

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
    def _cleared(self, time):
        okeq(self._state, 'clearing')
        self._state = 'ready'
