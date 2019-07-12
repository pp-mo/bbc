import sys

sys.path.append(
    '/storage/emulated/0/qpython/')
print('\n'.join(sys.path))

from sim.signal import Signal

# Test signals
x = Signal('x')
print(x)
x.trace()
x.set(5.0, 1)
x.set(6., 1)
x.untrace()
msg = 'x untraced, ={}'
print(msg.format(x.state))
x.set(0., 0)
print(msg.format(x.state))
