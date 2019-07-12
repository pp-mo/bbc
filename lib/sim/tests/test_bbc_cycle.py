from sim.bbc.controller import BbcController
from sim.signal import Signal
from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.tests import setsig

cycle = BbcController()
print(cycle)

sig_start = Signal('start')
sig_start.trace()
cycle.connect('start', sig_start)
cycle.current_phase.trace()
# cycle.trace('_do_phase')
for phase_name, _ in cycle.phase_names_and_default_durations:
    getattr(cycle, phase_name).trace()
SEQ.add(setsig(0.0, sig_start, '!'))
SEQ.run(100.0)