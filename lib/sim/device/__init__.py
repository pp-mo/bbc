from functools import wraps

import sys

path = '/storage/emulated/0/qpython/'
if path not in sys.path:
    sys.path.append(path)

from sim.sequencer import DEFAULT_SEQUENCER
from sim.signal import Signal


class Action(object):
    """
    Encode a delayed callback to an
    action method of a device, with
    given args and kwargs.
    
    Additional args/kwargs may be
    passed at calling time, if so
    they come first.
    (At present, in practice, just
    	the "time" arg.)

    """

    def __init__(self, device, funcname, *args, **kwargs):
        self.device = device
        self.funcname = funcname
        self._func = getattr(device, funcname)
        self.args = args
        self.kwargs = kwargs
        # msg = '\nTest print new {} action:\n  {}'
        # print(msg.format(self.__class__, self))

    def __str__(self):
        args = '...'
        if self.args:
            args = '.. '
            args += ','.join(str(x)
                             for x in self.args)
        if self.kwargs:
            kwargs = str(self.kwargs)
            kwargs = kwargs[1:-1]
            args += ',' + kwargs
        msg = 'Action<{}.{}({})>'.format(
            self.device.name,
            self.funcname,
            args)
        return msg

    def __call__(self, *args, **kwargs):
        args += self.args
        kwargs = self.kwargs.copy()
        kwargs.update(kwargs)
        # msg = 'call {} *{} **{}'
        # print msg. format (
        # 	  self._func, args, kwargs)
        return self._func(*args, **kwargs)


class Device(object):
    def __init__(self, name, sequencer=None):
        self.name = name
        self.seq = sequencer or DEFAULT_SEQUENCER
        self._traces = set()

    def __str__(self):
        return '{}<{}>'.format(
            self.__class__.__name__,
            self.name)

    def connect(self, input_name, signal):
        input_method = getattr(self, input_name)
        signal.add_connection(input_method)

    def add_output(self, name, start_value=None):
        full_name = '{}.{}'.format(
            self.name, name)
        signal = Signal(full_name, start_value)
        setattr(self, name, signal)
        # self.outputs[name] = signal

    @staticmethod
    def _trace_input(self, name, time, signal):
        if name not in self._traces:
            return
        msg = '@{}: INPUT<{}.{}> {} ==> {}'
        print(msg.format(
            time,
            self.name, name,
            signal.previous,
            signal.state))

    @staticmethod
    def input(f):
        name = f.__name__

        @wraps(f)
        def _wrapper(self, time, signal):
            self._trace_input(self, name, time, signal)
            return f(self, time, signal)

        return _wrapper

    @staticmethod
    def _trace_action(self, name, time, *args, **kwargs):
        if name not in self._traces:
            return
        argstrs = [str(time)]
        if args:
            argstrs.append(
                '*{}'.format(args))
        if kwargs:
            argstrs.append(
                '**{}'.format(kwargs))
        argstrs = ', '.join(argstrs)
        msg = '@{}: ACTION<{}.{}>({})'
        print(msg.format(
            time, self.name, name, argstrs))

    @staticmethod
    def action(f):
        name = f.__name__

        @wraps(f)
        def _wrapper(self, time, *args, **kwargs):
            self._trace_action(self, name, time, *args, **kwargs)
            return f(self, time, *args, **kwargs)

        return _wrapper

    def trace(self, name, on=True):
        getattr(self, name)
        if on:
            self._traces.add(name)
        else:
            self._traces.remove(name)

    def untrace(self, name):
        self.trace(name, False)


class ClockTick(Device):
    def __init__(self, name, period, *args, **kwargs):
        super(ClockTick, self).__init__(
            name, *args, **kwargs)
        self.period = period
        self.add_output('output')

    @Device.input
    def start(self, time, signal):
        # self._trace_input('start', time, signal)
        # Make a first tick happen.
        self.seq.add(
            (time,
             Action(self, 'tick')))

    @Device.action
    def tick(self, time):
        # self._trace_action('tick', time)
        self.output.set(time, 'Tick!')
        return (time + self.period,
                Action(self, 'tick'))


# utils, as assert disabled???
def okeq(a, b):
    if a != b:
        msg = '!Check fail: {!r} != {!r}.'
        msg = msg.format(a, b)
        raise ValueError(msg)


def okin(a, bs):
    if a not in bs:
        msg = '!Check fail: {!r} not in {!r}.'
        msg = msg.format(a, bs)
        raise ValueError(msg)
