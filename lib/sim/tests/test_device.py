import sys

sys.path.append(
    '/storage/emulated/0/qpython/')

from sim.signal import Signal
from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.device import Device, Action, ClockTick

# Test device (clock tick)
clk = ClockTick('clock_01', period=10)
print(clk)

startsig = Signal('start_clock')
clk.connect('start', startsig)
clk.trace('start')
clk.trace('tick')
clk.output.trace()


# input_hook(device, name, time, signal
def start_input_hook(device, time, signal):
    print('\n  =START-INPUT-HOOK: into {}.start : @{} = {}'.format(device.name, time, signal.state))

# action_hook(device, name, time, *args, **kwargs)
def tick_action_hook(device, time):
    print('\n  =TICK-ACTION-HOOK: into {}.tick @ {}'.format(device.name, time))

clk.hook('start', start_input_hook)
clk.hook('tick', tick_action_hook)
startsig.set(5, 'go')
SEQ.run(60)
