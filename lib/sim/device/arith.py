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
                 t_clear_onoff=4.,
                 t_eor_onoff=2.,
                 *args, **kwargs):
        super(PulseLatch, self).__init__(
            name, *args, **kwargs)
        self._t_0_1 = t_toggle_0_to_1
        self._t_1_0 = t_toggle_1_to_0
        self._t_carry = t_out_2_carry  # note: additional to t_out_delay
        self._t_clear = t_clear_onoff  # note: state to 0, do NOT emit a carry
        self._t_eor = t_eor_onoff  # control signal change
        #
        # inputs: 'input', 'enable_or', 'clear'
        # outputs: 'output', 'x_carry_out'
        # states:
        #    : idle, idle-with-clearing, value-toggling, carry-propagating,
        #    : dropping, controls-changing
        # transitions:
        #    'idle' --input>0--> 'value_toggling' --> [['carry-propagate' -->]] 'idle'
        #    'idle' --enable_or--> 'change-eor' --> idle
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
        self._clear_enabled = False

    @Device.input
    def input(self, time, signal):
        okin(self._state, ['idle', 'idle-with-clearing'])
        if signal.state == 0:
            # Ignore, in this case
            return
        if self._state == 'idle':
            self._state = 'value_toggling'
            if self._or_enabled:
                # In this mode, any input leaves us at '1'
                # (and we never emit carries).
                self._state = 1
            else:
                self._value = 1 - self._value  # invert store: -->output after delay
            self.output.set(time, SIG_UNDEF)
            toggle_delay = [self._t_0_1, self._t_1_0][self._value]
            self.act(time + toggle_delay, '_toggle_output')
        elif state == 'idle-with-clearing':
            self._state = 'dropping'  # Don't allow control change while dropping.
            self.act(time + self._t_drop, '_dropped')
        else:
            raise ValueError('input during unexpected state: {}'.format(self._state))

    @Device.action
    def _toggle_output(self, time):
        okeq(self.state, 'value_toggling')
        self.output.set(time, self._value)
        if self._value == 1:
            # New state is 1, no carry-out.
            self._state = 'idle'
        else:
            # Must also send a carry, before we are stable again.
            self.state = 'carry_propagating'
            self.seq.add(
                (time + self._t_carry,
                 Action(self, '_carry_out')))

    def _carry_out(self, time):
        okeq(self.state, 'carry_propagating')
        self._carry_out.set(time, 1)
        self.state = 'idle'

    @Device.input
    def enable_or(self, time, signal):
        okeq(self._state, 'idle')
        or_value = signal.state != 0
        if or_value == self._or_enabled:
            return
        # Internal stored-value and output are unaffected.
        # We just need a quiet moment to register the control change.
        self._or_enabled = or_value
        self._state = 'controls-changing'
        self.add(time + self._t_eor, '_control_changed', 'eor')

    @Device.input
    def clear(self, time, signal):
        okin(self._state, ['idle', 'idle-with-clearing'])
        clear_value = signal.state != 0
        if clear_value == self._clear_enabled:
            return
        self._clear_enabled = clear_value
        self._state = 'controls-changing'
        self.act(time + self._t_clear, '_control_changed', 'clear')
        if clear_value and self._value:
            # Also have a stored one to drop.
            self.output.set(time, SIG_UNDEF)
            self.act(time + self._t_carry, '_dropped')

    @Device.action
    def _control_changed(self, time, which_control):
        okeq(self._state, 'controls-changing')
        okin(which_control, ('eor', 'clear'))
        if which_control == 'clear' and self._clear_enabled:
            # Enter clearing mode.
            self._state = 'idle-with-clearing'
        else:
            # TODO: 'which_control' arg is redundant ??
            # FOR NOW: a useful test of 'act' extra args.
            okeq(self._clear_enabled, False)
            self._state = 'idle'

    @Device.action
    def _dropped(self, time):
        # Emit a dropped carry (and stabilise stored value = 0).
        okin(self._state,
             ['controls-changing', 'dropping'])
        # N.B. should NOT occur in 'idle' state.
        # N.B. no state change unless 'dropping'
        if self._state == 'dropping':
            # A special state, just to block control changes during 'dropping',
            # only entered when input arrives during 'idle-with-clearing'.
            self._state = 'idle-with-clearing'
        # 'ELSE' get here while clear goes 0 to 1 --> no state change.

        # Set stored-value stable.
        self.output.set(time, 0)
        # Send carry-out.
        self.x_carry_out.set(time, 1)
