from sim.device.latch import PulseLatch
from sim.sequencer import DEFAULT_SEQUENCER as seq
import sim.visualise
from sim.device.wire import Wire
from sim.signal import Signal

latch = PulseLatch('latch_1', bits=4, t_settle=5.0, t_out_delay=2.5)

sig_1 = Signal('sig_001')

latch.connect('input', sig1)
wire1 = Wire('wire_001', delay=7.0)
wire1.connect('input', latch.output)

import matplotlib.pyplot as plt

fig = plt.figure()
ax = plt.axes(figure=fig)
scene = sim.visualize.scene()

def add_viz(device, *args, **kwargs):
    # The 'view' function is a factory which associates supported subclasses of
    # sim.device.Device with matching subclasses of sim.visualise.DeviceView
    dev_view = sim.visualize.view(device, *args, **kwargs)
    scene.add(dev_view)

add_viz(latch,
        input=((0, 0), (4, 0)),
        output=((2, 5)),
        box_margin=0.5,
        box_color='#203040')

sig_1.set(0.0, 1)
seq.run(3.0)
scene.init()  # Create initial graphics
scene.animate(200.0)  # animate up to time point.

#
# Internal code to view actions.
#

from datetime.datetime import now as time_now

def viz(scene, from_seqtime=0.0, until_seqtime=None,
        frame_interval_secs=0.2, speedup_factor=1.0, pause_in_gaps=False):

    for view in scene.views:
        view.enable_draw(False)

    seq.run(from_seqtime)
    seq_time = from_seqtime

    # Do initial state plots.
    if scene.ax is None:
        scene.ax = plt.axes()
    ax = scene.ax
    for view in scene.views:
        view.enable_draw(True)
        view.init(ax)

    # Relate real time to sequence time
    actual_start_time = time_now()
    while (until_seqtime is None or seq_time < until_seqtime):
        next_actual_time = (actual_start_time +
                            (seq_time - from_seqtime) / speedup_factor +
                            frame_interval_secs)
        print('SIM-TIME : {:f7.3}'.format(seq_time))
        seq.run(seq_time)
        active_actions = False
        for view in scene.views:
            # Update all views before redraw
            active_actions |= bool(view.update(seq_time))
        ax.redraw()
        actual_time = time_now()
        ax.pause(next_actual_time - actual_time)
        if not active_actions:
            # No active visible changes.
            if len(seq.events) == 0:
                break  # Nothing more due to happen : Finished.
            if pause_in_gaps:
                # Wait for a key entry.
                print('  >> pause for key >> ')
                raw_input()
                # Skip forward to next actual event.
                seq_time = seq.events[0].time
                # Reset start-points of both seq and real times.
                from_seqtime = seq_time
                actual_start_time = time_now()
        seq_time += frame_interval_secs * speedup_factor


class DeviceView(object):
    def __init__(self, device, *args, **kwargs):
        self.dev = device
        self._connect(device)

    def init(self, matplotlib_axes):
        self.ax = matplotlib_axes

    def update(self, matplotlib_axes):
        pass

