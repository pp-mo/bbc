SIG_START_DEFAULT = 0
SIG_UNDEF = 'undefined'


class Signal(object):
    def __init__(self, name, start_state=None):
        self.name = name
        if start_state is not None:
            self.state = start_state
        else:
            self.state = SIG_START_DEFAULT
        self.previous = self.state
        self.conns = list()

    def __str__(self):
        msg = 'Sig<{}={}>'
        return msg.format(
            self.name, self.state)

    def set(self, time, state):
        self.previous = self.state
        self.state = state
        for conn in self.conns:
            # TODO: should really send only the state, not itself ??
            # current form for access to .state and .previous (?.name? : not really)
            # NEEDED for trace, in current form.  But device tracing is nicer ...
            conn(time, self)

    def add_connection(self, call, index=-1):
        self.conns[index:index] = [call]

    def remove_connection(self, call):
        while call in conns:
            self.conns.remove(call)

    def trace(self):
        self.add_connection(signal_trace, 0)

    def untrace(self):
        self.conns.remove(signal_trace)


def signal_trace(time, sig):
    msg = '@{}: Sig<{}> {} ==> {}'
    msg = msg.format(
        time,
        sig.name,
        sig.previous,
        sig.state)
    print(msg)


def trace(signal, on=True):
    if on:
        signal.add_connection(signal_trace)
    else:
        signal.conns.remove(signal_trace)


def untrace(signal):
    trace(signal, False)
