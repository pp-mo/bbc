import sys

sys.path.append(
    '/storage/emulated/0/qpython/')

from sim.signal import SIG_UNDEF
from sim.device import okeq, okin
from sim.device import Device, Action


class PulseRom(Device):
    """
    An addressable store with fixed
    read-only word contents.
    Event signal inputs for address
    select and release, and output
    trigger ("read" signal).

    """

    def __init__(self,
                 name,
                 rom_words,
                 t_addr_2_asel=1.0,
                 t_asel_2_read=1.0,
                 t_read_2_aclr=1.0,
                 t_aclr_2_addr=1.0,
                 t_out_delay=10.0,
                 *args, **kwargs):
        super(PulseRom, self).__init__(
            name, *args, **kwargs)
        self._rom = rom_words
        self._t_a2sel = t_addr_2_asel
        self._t_sel2rd = t_asel_2_read
        self._t_rd2clr = t_read_2_aclr
        self._t_clr2ad = t_aclr_2_addr
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
            (time + self._t_a2sel,
             Action(self, '_a_changed')))

    @Device.action
    def _a_changed(self, time):
        okeq(self._state, 'set-addr')
        self._state = 'idle'

    @Device.input
    def x_asel(self, time, signal):
        """
        Address enable input.
        Event triggered.
        """
        okeq(self._state, 'idle')
        self._state = 'enabling-address'
        self.seq.add(
            (time + self._t_sel2rd,
             Action(self,
                    '_a_enabled')))

    @Device.action
    def _a_enabled(self, time):
        okeq(self._state, 'enabling-address')
        self._state = 'active'

    @Device.input
    def x_read(self, time, signal):
        okeq(self._state, 'active')
        self._state = 'reading'
        # Note: does not block until
        # output, but do have a short
        # delay before clr is valid.
        index = min(
            self._addr,
            len(self._rom) - 1)
        data = self._rom[index]
        self.seq.addall([
            (time + self._t_delay,
             Action(self,
                    '_output_update',
                    data)),
            (time + self._t_rd2clr,
             Action(self,
                    '_read_done'))
        ])

    @Device.action
    def _read_done(self, time):
        # Thus just blocks a re-read
        # or clear too soon after read.
        okeq(self._state, 'reading')
        self._state = 'active'

    @Device.input
    def x_aclr(self, time, signal):
        okeq(self._state, 'active')
        self._state = 'disabling-address'
        self.seq.add(
            (time + self._t_clr2ad,
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
