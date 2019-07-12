import sys

sys.path.append(
    '/storage/emulated/0/qpython/')

from types import MethodType
from sim.signal import SIG_UNDEF
from sim.device import okeq, okin
from sim.device import Device, Action


class SigBitslice(Device):
    """
    A pseudo device that outputs
    a bit slice of an input signal.
    
    """

    def __init__(self,
                 name,
                 i_bit_0,
                 n_bits=1,
                 *args, **kwargs):
        super(SigBitslice, self).__init__(
            name, *args, **kwargs)
        self._i_bit_0 = i_bit_0
        self._mask = (2 ** n_bits) - 1
        self.add_output('output')

    @Device.input
    def input(self, time, signal):
        val = signal.state
        if isinstance(val,
                      (int, float)):
            val >>= self._i_bit_0
            val &= self._mask
        # "else" pass full input value
        # (e.g. typically, SIG_UNDEF)
        self.output.set(time, val)


def sig_bitslice(sig, ibit0,
                 nbits=1, name=None):
    if name is None:
        name = '{}:{}'.format(
            sig.name, ibit0)
    if nbits > 1:
        name += '..{}'.format(
            ibit0 + nbits - 1)
    result = SigBitslice(
        name, ibit0, nbits)
    result.connect('input', sig)
    return result


class SigJoin(Device):
    """
    Pseudo device to join signals
    into a single signal (buss).
    Output updates only once per
    input time, unless 'pass_all_events'
    is set.
    Input (methods) are created and
    added as required, by 'add_input'.
    
    """

    def __init__(self, name,
                 pass_all_events=False,
                 *args, **kwargs):
        super(SigJoin, self).__init__(
            name, *args, **kwargs)
        self._inputs = []
        self._input_bitwidths = []
        self.pass_all_events = pass_all_events
        self.add_output('output')
        self.reset()

    def add_input(self, signal, bitwidth):
        i_input = len(self._inputs)
        self._inputs.append(signal)
        self._input_bitwidths.append(
            bitwidth)

        def _inner(self, time, signal):
            self._input_event(
                i_input,
                time, signal.state)

        # fix the inner method name,
        # to enable tracing.
        in_name = 'in_{}'.format(
            str(i_input + 1))
        _inner.__name__ = in_name
        # wrap it as an input method
        new_method = Device.input(
            _inner)
        # convert it to an instance method
        new_method = MethodType(
            new_method, self)
        # attach to the instance
        setattr(
            self,
            in_name,
            new_method)
        self.connect(in_name, signal)
        self.reset()

    def reset(self):
        self._state = 'idle'

    def _input_event(
            self, i_in, time, state):

        if self._state == 'idle':
            self._state = 'get-updates'
            self._time = time
            if self.pass_all_events:
                # just do it now
                self._update_output(
                    time)
            else:
                # schedule an update after
                # all 'normal' events
                # at this timepoint.
                self.seq.add(
                    ((time, -9999),
                     Action(self,
                            '_update_output')
                     )
                )
        else:
            okeq(self._state, 'get-updates')
            okeq(time, self._time)

    @Device.action
    def _update_output(self, time):
        okeq(self._state, 'get-updates')
        okeq(time, self._time)
        val = 0
        for sig, width in zip(
                self._inputs,
                self._input_bitwidths):
            this = sig.state
            if not isinstance(
                    this,
                    (int, float)):
                val = SIG_UNDEF
                break
            else:
                mask = (2 ** width) - 1
                this = int(this) & mask
                val <<= width
                val |= this
        self.output.set(time, val)
        self._state = 'idle'


def sig_join(name, sigs_and_bitwidths):
    dev = SigJoin(name)
    for sig, width in sigs_and_bitwidths:
        dev.add_input(sig, width)
    return dev


class SigSendCopy(Device):
    def __init__(self, *args, **kwargs):
        super(SigSendCopy, self).__init__(*args, **kwargs)
        self.output = self.add_output('output')
        self._state = SIG_UNDEF

    @Device.input
    def input(self, time, signal):
        # Grab the latest value of the input
        # NOTE: the definition of device "connection" doesn't give us access to
        # the connected signal -- we only see "events".
        self._state = signal.state

    @Device.input
    def send(self, time, signal):
        # Trigger an output event
        self.output.set(self._state)

