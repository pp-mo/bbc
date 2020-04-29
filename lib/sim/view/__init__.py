"""Resources for making animation views of sim.device.Device objects."""
from __future__ import print_function
from datetime import datetime, timedelta
import six
import six.moves

import matplotlib.pyplot as plt


time_now = datetime.now

class DeviceView(object):
    target_devicetype = None  # Set to expected class of wrapped device.

    def __init__(self, device, *args, **kwargs):
        self.dev = device
        assert isinstance(device, self.target_devicetype)
        self.animate = None

    def hook_device_calls(self, name_or_names):
        """
        Install hooks into target device method calls.

        May be 'input' or 'action' methods (but call signatures differ).
        The hooks call into the same-named methods of the caller, which must
        therefore exist and have compatible signatures.

        """
        if isinstance(name_or_names, six.text_type):
            names = [name_or_names]
        else:
            names = name_or_names

        for name in names:
            self.dev.hook(name, getattr(self, name))

    def enable_draw(self, on=True):
        self._enable_draw = on

    def ani_init(self, matplotlib_axes):
        """
        Create a matplotlib drawing of the device.

        On the specified matplotlib.Axes.

        """
        self.ax = matplotlib_axes

    def ani_updated_state(self, seq_time):
        """
        Return a modified animation state for a time point.

        The result can be passed in to ani_apply.

        """
        return None


    @staticmethod
    def _get_element_state(element, AniDataType):
        # 'element' is a visible matplotlib graphics object.
        # AniDataType is a SlotsHolder whose slot_names are the names of the
        # element attributes we want to adjust during an animation.
        # ( NOTE: which *must* all have 'get_' and 'set_' methods )
        # We return an 'AniDataType' filled with the current settings.
        result = AniDataType()
        for propname in AniDataType.slot_names:
            get_method = getattr(element, 'get_' + propname)
            value = get_method()
            setattr(result, propname, value)
        return result

    def ani_apply_state(self, anim):
        """
        Update the device drawing, by changing artist properties.

        Called in preparation for an Axes.redraw().
        The operation works in conjunction with the stored current state,
        self._anidata, to transition into any given state on request.
        This allows us to rewind to / replay from any point in an animation.

        """
        # anim is a specific SlotsHolder subclass, where :
        #   anim[element_name] --> graphics_element
        #       - and getattr(self, slot) is a graphical element
        # each graphics_element is a SlotsHolder subclass, where :
        #   element[property_name] --> property_value
        #       - and getattr(element, 'set_' + property_name) is a method
        for element_name in anim.slot_names:
            element = getattr(self, element_name)  # A graphics component
            new_settings = getattr(anim, element_name)  # Its required state
            old_settings = getattr(self._anidata, element_name)
                # Its current state (as we have it recorded)
            if new_settings != old_settings:
                for prop_name in new_settings.slot_names:
                    set_value = getattr(new_settings, prop_name)
                    old_value = getattr(old_settings, prop_name)
                    if set_value != old_value:
                        method = getattr(element, 'set_' + prop_name)
                        method(set_value)
        # Record the new current state
        self._anidata = anim



#
# Key routine to perform animation.
#
def viz(views, from_seqtime=0.0, until_seqtime=None,
        axes=None,
        frame_interval_secs=0.2, speedup_factor=1.0,
        pause_in_gaps=False, skip_gaps=False, pause_every_step=False):
    """
    The key visual animation routine.

    Args:

    * views (list of DeviceView objects):
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
    * pause_every_step (bool):
        Pause for keypress at every update.
    * skip_gaps (bool):
        If set, jump over gaps when all is idle.
        Like 'pause_in_gaps' but with no pause for input.

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
        view.ani_init(ax)

    plt.autoscale()

    # Relate real time to sequence time
    actual_start_time = time_now()
    while (until_seqtime is None or seq_time < until_seqtime):
        seqtime_relative = (seq_time - from_seqtime) / speedup_factor
        next_actual_time = (
            actual_start_time +
            timedelta(seconds=seqtime_relative + frame_interval_secs))
        # print('\rSIM-TIME : {:8.3f}    | '.format(seq_time), end='')
        print('SIM-TIME : {:8.3f}    | '.format(seq_time))
        seq.run(seq_time)
        active_actions = False
        for view in views:
            # Update all views before redraw
            anidata = view.ani_updated_state(seq_time)
            if anidata is not None:
                view.ani_apply_state(anidata)
                active_actions = True
        plt.draw()
        actual_time = time_now()
        pause_seconds = (next_actual_time - actual_time).total_seconds()
        pause_seconds = max(pause_seconds, 0.1 * frame_interval_secs)
        plt.pause(pause_seconds)
        if active_actions and pause_every_step:
            # Wait for a key entry (but not if gap is coming)
            print('\n >>STEP>> pause for key.. \n')
            six.moves.input()
        if not active_actions:
            # No active visible changes.
            if len(seq.events) == 0:
                break  # Nothing more due to happen : Finished.
            if pause_in_gaps or pause_every_step or skip_gaps:
                if pause_in_gaps or pause_every_step:
                    # Wait for a key entry.
                    print('\n >>GAP>> pause for key.. \n')
                    six.moves.input()
                # Skip forward to next actual event.
                seq_time = seq.events[0].time
                # Reset start-points of both seq and real times.
                from_seqtime = seq_time
                actual_start_time = time_now()
        seq_time += frame_interval_secs * speedup_factor

    return ax
