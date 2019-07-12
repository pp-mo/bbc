class Event(object):
    def __init__(self, evdata):
        time, call = evdata
        if hasattr(time, '__getitem__'):
            # ev=((time, priority), call)
            time, priority = time
        else:
            # ev=(time, call)
            priority = 0
        self.time = time
        self.priority = priority
        self.call = call

    def key(self):
        # priority separates events
        # at same time, for which
        # higher numbers come first.
        return (self.time,
                -self.priority)

    def __repr__(self):
        msg = 'Event<@({},{}): {}>'
        msg = msg.format(
            self.time, self.priority,
            self.call)
        return msg


def _make_event(evdata):
    if not isinstance(evdata, Event):
        evdata = Event(evdata)
    return evdata


class Sequencer(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.events = []

    def add(self, event):
        # print 'add:{}'.format(event)
        event = _make_event(event)
        events = self.events + [event]
        events = sorted(events,
                        key=lambda ev: ev.key())
        self.events = events

    def addall(self, events):
        # print 'addall:{}'.format(events)
        if events:
            if not isinstance(events, list):
                events = [events]
            for ev in events:
                self.add(ev)

    def run(self, stop=None):
        while len(self.events) > 0:
            event = self.events[0]
            time = event.time
            if (stop is not None and
                    time > stop):
                break
            self.events = self.events[1:]
            new_evs = event.call(time)
            self.addall(new_evs)


# Default sequencer
DEFAULT_SEQUENCER = Sequencer()
