# Accumulator and adder arithmetic

from sim.signal import SIG_UNDEF
from sim.device import okeq, okin
from sim.device import Device, Action


class CounterOnebit(Device):
    """
    A one-bit store with increment-toggle, carry-out and async clear.

    'Clear' is effectively an operation *mode*, not an event-triggered
    operation :  While clear is active, an incoming '1' is "dropped".
    So, it is valid to receive input when clear is high, represented by the
    state == 'idle-with-clearing'.  But, it is still an error to get input
    before the clear signal has "settled", i.e. state == 'controls-changing'.

    Note: also supports an 'or_enable' control input (which prevents a '1'
    toggling back to a '0').  But this is only for convenience in constructing
    a full 'Accumulator' implementation :  The derived multi-bit 'Counter'
    device does *not* provide an `or_enable` input.

    """
    def __init__(self, name,
                 t_toggle_0_to_1=3.,
                 t_toggle_1_to_0=3.,
                 t_out_2_carry=1.,
                 t_clear_2_carry=2.,
                 t_clear_onoff=4.,
                 t_eor_onoff=2.,
                 *args, **kwargs):
        super(CounterOnebit, self).__init__(
            name, *args, **kwargs)
        self._t_0_1 = t_toggle_0_to_1
        self._t_1_0 = t_toggle_1_to_0
        self._t_carry = t_out_2_carry  # note: additional to t_out_delay
        self._t_clear = t_clear_onoff  # note: state to 0, do NOT emit a carry
        self._t_eor = t_eor_onoff  # control signal change
        if (t_clear_onoff < t_clear_2_carry):
            msg = (
                't_clear_onoff({}) < t_clear_2_carry({}) : disallowed, as '
                'clear must complete before return to idle mode.')
            raise ValueError(msg.format(t_clear_onoff, t_clear_2_carry))
        self._t_drop = t_clear_2_carry
        #
        # inputs: 'input', 'enable_or', 'clear'
        # outputs: 'output', 'x_carry_out'
        # states:
        #    : idle, idle-with-clearing, value-toggling, carry-propagating,
        #    : dropping, controls-changing
        # transitions:
        #    'idle' -- (input>0) --> 'value-toggling' -->
        #        --> [ 'carry-propagate' --> ] 'idle'
        #    'idle-with-clearing' --input>0--> 'dropping'
        #        --> 'idle-with-clearing
        #    ['idle' | 'idle-with-clearing' | 'controls-changing']
        #        -- (enable_or OR clear) -->
        #        --> 'controls-changing'
        #        --> ['idle' | 'idle-with-clearing']
        # outputs:
        #   output: update after 't_toggle_X_to_Y'
        #   carry-out: after 't_toggle_X_to_Y' + 't_out_2_carry'
        #
        # Value 'state' is available at the output (state driven).
        # Carry-out is strictly event-mode, always sends value=1.
        # Clearing sends a carry, if a '1' is in store.
        self.add_output('output', start_value=0)
        self.add_output('x_carry_out')
        self.reset()

    def reset(self):
        self._state = 'idle'
        self._value = 0
        self._or_enabled = False
        self._clear_enabled = False
        self._or_changing = False
        self._clear_changing = False
        self._n_control_changes_due = 0

    @Device.input
    def input(self, time, signal):
        okin(self._state, ['idle', 'idle-with-clearing'])
        if signal.state == 0:
            # Ignore, in this case
            return
        self.output.set(time, SIG_UNDEF)
        if self._state == 'idle':
            self._state = 'value-toggling'
            toggle_delay = [self._t_0_1, self._t_1_0][self._value]
            if self._or_enabled:
                # In this mode, any input leaves us at '1'
                # (and we never emit carries).
                # Note: delay is the same, but will not then emit a carry.
                self._value = 1
            else:
                self._value = 1 - self._value  # invert --> output after delay
            self.act(time + toggle_delay, '_toggle_output')
        elif self._state == 'idle-with-clearing':
            self._state = 'dropping'  # Block control changes while dropping.
            self.act(time + self._t_0_1 + self._t_drop, '_dropped')
        else:
            assert False  # should never be able to get here.

    @Device.action
    def _toggle_output(self, time):
        okeq(self._state, 'value-toggling')
        self.output.set(time, self._value)
        if self._value == 1:
            # New state is 1, no carry-out.
            self._state = 'idle'
        else:
            # Must also send a carry, before we are stable again.
            self._state = 'carry-propagating'
            self.act(time + self._t_carry, '_carry_out')

    def _carry_out(self, time):
        okeq(self._state, 'carry-propagating')
        self.x_carry_out.set(time, 1)
        self._state = 'idle'

    @Device.input
    def enable_or(self, time, signal):
        or_value = signal.state != 0
        if or_value == self._or_enabled:
            return
        okin(self._state, ['idle', 'idle-with-clearing', 'controls-changing'])
        okeq(self._or_changing, False)
        # Internal stored-value and output are unaffected.
        # We just need a quiet moment to register the control change.
        self._state = 'controls-changing'
        # record new value of control.
        self._or_enabled = or_value
        # prevent overlapping change on same input.
        self._or_changing = True
        # count control changes to allow multiple controls within a change.
        self._n_control_changes_due += 1
        self.act(time + self._t_eor, '_control_changed')

    @Device.input
    def clear(self, time, signal):
        clear_value = signal.state != 0
        if clear_value == self._clear_enabled:
            return
        okin(self._state, ['idle', 'idle-with-clearing', 'controls-changing'])
        okeq(self._clear_changing, False)
        self._state = 'controls-changing'
        # record new value of control.
        self._clear_enabled = clear_value
        # prevent overlapping change on same input.
        self._clear_changing = True
        # count control changes to allow multiple controls within a change.
        self._n_control_changes_due += 1
        self.act(time + self._t_clear, '_control_changed')
        if clear_value and self._value:
            # Also have a stored '1' to drop.
            self.output.set(time, SIG_UNDEF)
            self.act(time + self._t_drop, '_dropped')

    @Device.action
    def _control_changed(self, time):
        okeq(self._state, 'controls-changing')
        # countdown n control changes to end of change period.
        self._n_control_changes_due -= 1
        if self._n_control_changes_due == 0:
            # Last of 'N' control changes --> change period delay is over.
            # Reset the interlocks preventing >1 change on the same input.
            self._or_changing = False
            self._clear_changing = False
            # Return to 'idle' or 'clearing' state.
            if self._clear_enabled:
                self._state = 'idle-with-clearing'
            else:
                self._state = 'idle'

    @Device.action
    def _dropped(self, time):
        # Emit a dropped '1' as a carry (and stabilise stored value = 0).
        okin(self._state, ['controls-changing', 'dropping'])
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
