# Accumulator and adder arithmetic

from sim.signal import SIG_UNDEF
from sim.device import okeq, okin
from sim.device import Device, Action


class CounterOnebit(Device):
    """
    A one-bit store with increment-toggle, carry-out and async clear.

    """
    def __init__(self, name,
                 t_toggle_0_to_1=3.,
                 t_toggle_1_to_0=3.,
                 t_out_2_carry=1.,
                 t_clear=4.,
                 t_set_eor=2.,
                 *args, **kwargs):
        super(PulseLatch, self).__init__(
            name, *args, **kwargs)
        self._t_0_1 = t_toggle_0_to_1
        self._t_1_0 = t_toggle_1_to_0
        self._t_carry = t_out_2_carry  # note: additional to t_out_delay
        self._t_clear = t_clear  # note: state to 0, do NOT emit a carry
        self._t_eor = t_set_eor  # control signal change
        #
        # inputs: 'input', 'enable_or', 'x_clear'
        # outputs: 'output', 'x_carry_out'
        # states:
        #    'idle' --input>0--> 'changing' --> [['carry-propagate' -->]] 'idle'
        #    'idle' --enable_or--> 'control-change' --> idle
        #    'idle' --clear--> 'clearing' --> idle
        #  output: update after t_toggle_X_to_Y + t_out_delay
        #  carry-out: after t_toggle_X_to_Y + t_out_delay + t_out_2_carry
        # 'state' is available at the output (state driven).
        #  carry-out is strictly event-mode, always sends value=1.
        # clearing sends a carry, if '1' stored.
        self.add_output('output', start_value=0)
        self.add_output('x_carry_out')
        self.reset()

    def reset(self):
        self._state = 'idle'
        self._value = 0
        self._or_enabled = False

    @Device.input
    def input(self, time, signal):
        okeq(self._state, 'idle')
        if signal.state == 0:
            # Ignore, in this case
            return
        self._state = 'changing'
        if self._or_enabled:
            # In this mode, any input leaves us at '1'
            # (and we never emit carries).
            self._state = 1
        else:
            self._value = 1 - self._value  # invert store: -->output after delay
        self.output.set(time, SIG_UNDEF)
        toggle_delay = [self._t_0_1, self._t_1_0][self._value]
        self.seq.add(
            (time + toggle_delay,
             Action(self, '_update_output')))

    @Device.action
    def _update_output(self, time):
        okeq(self.state, 'changing')
        self.output.set(time, self._value)
        if self._value == 1:
            # New state is 1, no carry-out.
            self._state = 'idle'
        else:
            # Must also send a carry, before we are stable again.
            self.state = 'carry_propagate'
            self.seq.add(
                (time + self._t_carry,
                 Action(self, '_carry_out')))

    def _carry_out(self, time):
        okeq(self.state, 'carry_propagate')
        self._carry_out.set(time, 1)
        self.state = 'idle'

    @Device.input
    def enable_or(self, time, signal):
        okeq(self._state, 'idle')
        # Internal state and output are unaffected.
        # We just need a quiet moment to register the control change.
        self._state = 'control-change'
        self._or_enabled = (signal.state != 0)
        self.seq.add((time + self._t_eor,
                      Action(self, '_eor_set')))

    @Device.action
    def _eor_set(self, time):
        okeq(self._state, 'control-change')
        # We can now allow operation again.
        self._state = 'idle'

    @Device.input
    def x_clear(self, time, signal):
        okeq(self._state, 'idle')
        self._state = 'clearing'
        self.output.set(time, SIG_UNDEF)
        self.seq.add(
            (time + self._t_clear,
             Action(self, '_cleared'))

    @Device.action
    def _cleared(self, time):
        okeq(self._state, 'clearing')
        cleared_value = self._value
        # Set output to 0.
        self.output.set(time, 0)
        if self._value == 0:
            # No bit stored : Done.
            self._state = 'idle'
        else:
            # Stored bit produces carry-output, before returning to idle.
            self._value = 0
            self._state = 'carry-propagate'  # Same route as normal carry.
            self.seq.add((time + self._t_carry),
                         Action(self, 'carry_out'))

