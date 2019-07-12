# test utils

from sim.device import okeq, okin


# util, needs a place to live
def setsig(time, sig, val):
    def _call(t):
        sig.set(t, val)

    return (time, _call)


from contextlib import contextmanager


@contextmanager
def fails(cls=Exception, show=True):
    try:
        err = None
        yield
    except cls as err:
        pass
    if err is None:
        msg = 'Expected error {} not seen.'
        if cls is Exception:
            cls = ''
        else:
            cls = str(cls)
        msg = msg.format(cls)
        raise Exception(msg)
    if show:
        msg = 'Caught expected error:\n  {}'
        print(msg.format(err))
