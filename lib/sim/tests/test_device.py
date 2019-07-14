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
startsig.set(5, 'go')
SEQ.run(60)
