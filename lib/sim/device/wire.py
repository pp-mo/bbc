from sim.signal import Signal, SIG_UNDEF
from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.device import Device, Action, ClockTick


class Wire(Device):
    def __init__(self,
                 name, delay=1, startval=None,
                 *args, **kwargs):
        super(Wire, self).__init__(
            name, *args, **kwargs)
        self.delay = delay
        self.add_output(
            'output', startval)

    @Device.input
    def input(self, time, signal):
        state = signal.state
        if state != signal.previous:
            # output ok till change?
            # self.output.set(SIG_UNDEF)
            self.seq.add((
                time + self.delay,
                Action(self,
                       '_set_delay',
                       signal.state)))

    @Device.action
    def _set_delay(self, time, state):
        # msg = '!set_delay({}, {})'
        # print msg. format (
        #    time, state)
        self.output.set(time, state)
