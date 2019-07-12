from sim.signal import SIG_UNDEF
from sim.device import okeq, okin
from sim.device import Device, Action


class PulseRam(Device):
    """
    An addressable store with read/write word contents.
    Event signal inputs for address-select (=read) and -release.
    Input captures new (write) data, allowed just once after read + before release.

    """

    def __init__(self,
                 name,
                 t_addr_2_read=1.0,
                 t_read_2_write_or_aclr=1.0,
                 t_write_2_aclr=1.0,
                 t_aclr_2_addr=1.0,
                 t_out_delay=5.0,
                 *args, **kwargs):
        super(PulseRam, self).__init__(
            name, *args, **kwargs)
        # Initialise RAM content.
        # NOTE: don't bother with full map, store written words + assume rest=0
        self._ram_content = {}
        self._t_a2r = t_addr_2_read
        self._t_r2wc = t_read_2_write_or_aclr
        self._t_w2c = t_write_2_aclr
        self._t_c2a = t_aclr_2_addr
        self._t_delay = t_out_delay
        # Output word. Generates
        # events, not state-based.
        self.add_output('out')
        self.reset()

    def reset(self):
        self._state = 'idle'
        self._addr = 0

    @Device.input
    def addr(self, time, signal):
        """Address input."""
        okeq(self._state, 'idle')
        self._state = 'set-addr'
        self._addr = signal.state
        self.seq.add(
            (time + self._t_a2r,
             Action(self, '_a_changed')))

    @Device.action
    def _a_changed(self, time):
        okeq(self._state, 'set-addr')
        self._state = 'idle'

    @Device.input
    def x_read(self, time, signal):
        """
        Address enable input.
        Event triggered.
        """
        okeq(self._state, 'idle')
        self._state = 'reading'
        value = self._ram_content.get(self._addr, 0)
        self._ram_content[self._addr] = 0
        self.seq.addall([
            (time + self._t_r2wc,
             Action(self, '_read_done')),
            (time + self._t_delay,
             Action(self, '_output_update', value))
        ])

    @Device.action
    def _read_done(self, time):
        # Thus just blocks a re-read
        # or clear too soon after read.
        okeq(self._state, 'reading')
        self._state = 'read-but-not-written'

    @Device.input
    def d_in(self, time, signal):
        okeq(self._state, 'read-but-not-written')
        self._state = 'writing'
        self.seq.add((time + self._t_w2c,
                      Action(self, '_write_done')))
        value = signal.state
        okeq(isinstance(value, (int, float)), True)
        self._ram_content[self._addr] = int(value)

    @Device.action
    def _write_done(self, time):
        okeq(self._state, 'writing')
        self._state = 'read-and-written'

    @Device.input
    def x_aclr(self, time, signal):
        okin(self._state, ('read-but-not-written', 'read-and-written'))
        self._state = 'disabling-address'
        self.seq.add(
            (time + self._t_c2a,
             Action(self,
                    '_a_cleared')))

    @Device.action
    def _a_cleared(self, time):
        okeq(self._state, 'disabling-address')
        self._state = 'idle'

    @Device.action
    def _output_update(self, time, word):
        # Note: output updates after
        # a delay, quite separate from
        # internal state changes.
        self.out.set(time, word)
