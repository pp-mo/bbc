"""Resources for making animation views of sim.device.Device objects."""
from datetime import datetime, timedelta

import matplotlib.pyplot as plt


time_now = datetime.now

class DeviceView(object):
    def __init__(self, device, *args, **kwargs):
        self.dev = device
        self.animate = None

    def hook_device_calls(self, name_or_names):
        """
        Install hooks into target device method calls.

        May be 'input' or 'action' methods (but call signatures differ).
        The hooks call into the same-named methods of the caller, which must
        therefore exist and have compatible signatures.

        """
        if isinstance(name_or_names, basestring):
            names = [name_or_names]
        else:
            names = name_or_names

        for name in names:
            self.dev.hook(name, getattr(self, name))

    def enable_draw(self, on=True):
        self._enable_draw = on

    def init(self, matplotlib_axes):
        """
        Create a matplotlib drawing of the device.

        On the specified matplotlib.Axes.

        """
        self.ax = matplotlib_axes

    def update(self, seq_time):
        """
        Update the device drawing, by changing artist properties.

        Called in preparation for an Axes.redraw().

        """
        return self.animate != None


#
#
#

from sim.view.latch_view import PulseLatchView
_DEVICE_CLASSNAMES_AND_VIEW_CLASSES = {
    'PulseLatch': PulseLatchView
}

def device_view(device, *args, **kwargs):
    """
    A factory method for creating a DeviceView for a device.

    Returns an object of the appropriate linked DeviceView class in each case,
    passing all additional arguments to that.

    """
    return _DEVICE_CLASSNAMES_AND_VIEW_CLASSES[device.__class__.__name__](
        device, *args, **kwargs)


#
# Key routine to perform animation.
#
def viz(views, from_seqtime=0.0, until_seqtime=None,
        axes=None,
        frame_interval_secs=0.2, speedup_factor=1.0, pause_in_gaps=False):
    """
    The key visual animation routine.

    Args:

    * scene (list of DeviceView objects):
        The device viewers to be animated.
    * from_seqtime (float):
        The sequencer time to run the sequencer to before starting animation.
    * until_seqtime (float):
        The sequencer time to stop at.  If not set, animation only stops when
        the sequence is empty, and all view.update() calls return None.
    * axes (matplotlib.Axes or None):
        A pre-exising axes to draw on.  If None, one is created.
    * frame_interval (float):
        The real-time interval between visual updates.
    * speedup_factor (float):
        Ratio between actual animation time and sequencer time.
    * pause_in_gaps (bool):
        If set, pause on keypress when all view.update()s are idle, then skip
        ahead immediately to the next sequencer event.
        # ?? to the start of the next animation ??

    Returns:
        The 'axes' used, which was created if not passed in.

    Each view in the scene will contain a device.  All these must share the
    same sequencer, which should be pre-loaded with initial events so that it
    can simply be run.  The sequencer is pre-run to 'from_seqtime' before
    animation begins, and is then animated until 'from_time', or all activity
    has finished (all views idle).

    """
    for view in views:
        view.enable_draw(False)

    seq = views[0].dev.seq
    seq.run(from_seqtime)
    seq_time = from_seqtime

    # Do initial state plots.
    ax = axes or plt.axes()

    for view in views:
        view.enable_draw(True)
        view.init(ax)

    plt.autoscale()

    # Relate real time to sequence time
    actual_start_time = time_now()
    while (until_seqtime is None or seq_time < until_seqtime):
        seqtime_relative = (seq_time - from_seqtime) / speedup_factor
        next_actual_time = (
            actual_start_time +
            timedelta(seconds=seqtime_relative + frame_interval_secs))
        print('SIM-TIME : {:07.3f}'.format(seq_time))
        seq.run(seq_time)
        active_actions = False
        for view in views:
            # Update all views before redraw
            active_actions |= bool(view.update(seq_time))
        plt.draw()
        actual_time = time_now()
        pause_seconds = (next_actual_time - actual_time).total_seconds()
        pause_seconds = max(pause_seconds, 0.1 * frame_interval_secs)
        plt.pause(pause_seconds)
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

    return ax