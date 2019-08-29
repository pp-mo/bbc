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

#
# Common viewer baseclass
#

class DeviceView(object):
    def __init__(self, device, *args, **kwargs):
        self.dev = device
        self.els = {}  # storage for graphical elements
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


from matplotlib.patches import Polygon, Circle
from matplotlib.text import Text

class PulseLatchView(DeviceView):
    def __init__(self, device, input_xy, output_xy,
                 min_halfwidth=4.0, min_halfheight=6.0,
                 outline_poly_kwargs=None,
                 value_text_kwargs=None,
                 onebit_mode=False, onebit_circle_kwargs=None):
        assert isinstance(device, PulseLatch)
        super(PulseLatchView, self).__init__(device)
        self.input_x, self.input_y = input_xy
        self.output_x, self.output_y = output_xy
        self.min_hh = min_halfheight
        self.min_hw = min_halfwidth
        self.outline_poly_kwargs = (outline_poly_kwargs or
            {'color':'red', 'linewidth':1.5})
        self.value_text_kwargs = value_text_kwargs
        self.onebit_mode = onebit_mode
        self.onebit_circle_kwargs = (onebit_circle_kwargs or
            {'facecolor':'blue', 'radius':4.0,
             'edgecolor':'black', 'linewidth':1.5})
        self.hook_device_calls(('input', 'clr'))

    def init(self, axes):
        self.ax = axes
        self.centre_x = 0.5 * (self.input_x + self.output_x)
        min_x = min(self.input_x, self.output_x)
        max_x = max(self.input_x, self.output_x)
        if (max_x - min_x) < (2 * self.min_hw):
            min_x = centre_x - self.min_hw
            max_x = centre_x + self.min_hw
        self.centre_y = 0.5 * (self.input_y + self.output_y)
        min_y = min(self.input_y, self.output_y)
        max_y = max(self.input_y, self.output_y)
        if (max_y - min_y) < (2 * self.min_hh):
            min_y = centre_y - self.min_hh
            max_y = centre_y + self.min_hh

        self.upper_y = 0.25 * self.centre_y + 0.75 * max_y

        coords = np.array([[min_x, max_x, max_x, min_x],
                           [min_y, min_y, max_y, max_y]],
                          dtype=np.float)
        coords = coords.transpose())
        poly = Polygon(xy=coords, closed=True,
                       color=self.outline_color,
                       linewidth=self.linew,
                       **self.outline_poly_kwargs)
        self.ax.add_patch(poly)
        self.els['box_poly'] = poly

        if self.onebit_mode:
            # Make a circle to show the 'blob'.
            circ = Circle(
                xy=(centre_x, centre_y),
                axes=self.ax, **self.onebit_circle_kwargs)
            self.ax.add_patch(circ)
            self.els['blob_circle'] = circ
        else:
            # Make a text to show the value.
            txt = Text(
                x=centre_x, y=centre_y, text=self.content_text,
                verticalalignment='center', horizontalalignment='center'
                **self.value_text_kwargs)
            self.ax.add_patch(txt)
            self.els['value_text'] = txt

    def input(self, device, seq_time, signal):
        if signal.state != 0:
            # Start a capture animation.
            self.animate = 'capture'
            self.anim_start = seq_time
            self.anim_duration = self.dev._t_d2c
            self.anim_end = time + self.anim_duration
            self.els['value_text'].set_text(str(signal.state))
            self.els['value_text'].set_fontproperties(
                style='italic', weight='bold')
            self.els['value_text'].set_y(self.upper_y)

    def clr(self, device, time, signal):
        # Start a clear-content animation.
        self.animate = 'clear'
        self.anim_start = seq_time
        self.anim_duration = self.dev._t_d2c
        self.anim_end = time + self.anim_duration
        self.x_wobble_phases = 12 # out+back 3 times in each direction
        self.x_wobble_phase_time = self.anim_duration / self.x_wobble_phases
        self.els['value_text'].set_text('--XXX--')
        self.els['value_text'].set_fontproperties(style='italic')
        self.els['value_text'].set_color('red)

    def _phase_to_fract(self, time):
        cycle = (time - self.anim_start) / self.x_wobble_phase_time
        phase = int(np.floor(cycle % 4.0))
        fract = cycle % 1.0
        if phase == 0:
            result = fract
        elif phase == 1:
            result = 1.0 - fract
        elif phase == 2:
            result = 0.0 - fract
        elif phase == 3:
            result = -1.0 + fract
        else:
            assert phase in [0, 1, 2, 3]
        return result

    def update(self, seq_time):
        """Update drawn elements for animation"""
        if self.animate == 'capture':
            if seq_time < self.anim_end:
                fract = (seq_time - self.anim_start) / self.anim_duration
                y_at = (self.upper_y + 
                        fract * (self.centre_y - self.upper_y))
                self.els['value_text'].set_y(y_at)
            else:
                # Restore 'normality' + stop animation
                self.els['value_text'].set_y(self.centre_y)
                self.els['value_text'].set_fontproperties(
                    style='normal', weight='normal')
                self.animate = None
        elif self.animate == 'clear':
            if seq_time < self.anim_end:
                fract = self._phase_to_fract(seq_time)
                x_at = (self.centre_x - self.min_hw + 
                        fract * 2 * self.min_hw)
                self.els['value_text'].set_x(x_at)
            else:
                # Restore 'normality' + stop animation
                self.els['value_text'].set_x(self.centre_x)
                self.els['value_text'].set_text('---')
                self.els['value_text'].set_color('black')
                self.els['value_text'].set_fontproperties(
                    style='normal', weight='normal')
                self.animate = None

        return self.animate is not None


#
# View creation factory
#
_device_and_view_classes = {
    'PulseLatch': PulseLatchView
}

def device_view(device, *args, **kwargs):
    return _device_and_view_classes[device.__class__.__name__](
        device, *args, **kwargs)

