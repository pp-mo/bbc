import numpy as np
from matplotlib.patches import Polygon, Circle
from matplotlib.text import Text
from matplotlib.font_manager import FontProperties

from sim.view import DeviceView
from sim.device.latch import PulseLatch


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
            {'edgecolor':'red', 'linewidth':1.5})
        self.value_text_kwargs = value_text_kwargs or {}
        self.onebit_mode = onebit_mode
        self.onebit_circle_kwargs = (onebit_circle_kwargs or
            {'facecolor':'blue', 'radius':4.0,
             'edgecolor':'black', 'linewidth':1.5})
        self.hook_device_calls(('input', 'clr'))
        self.value_text_unset = '---'

    def init(self, axes):
        self.ax = axes
        self.centre_x = 0.5 * (self.input_x + self.output_x)
        min_x = min(self.input_x, self.output_x)
        max_x = max(self.input_x, self.output_x)
        if (max_x - min_x) < (2 * self.min_hw):
            min_x = self.centre_x - self.min_hw
            max_x = self.centre_x + self.min_hw
        self.centre_y = 0.5 * (self.input_y + self.output_y)
        min_y = min(self.input_y, self.output_y)
        max_y = max(self.input_y, self.output_y)
        if (max_y - min_y) < (2 * self.min_hh):
            min_y = self.centre_y - self.min_hh
            max_y = self.centre_y + self.min_hh

        self.upper_y = 0.25 * self.centre_y + 0.75 * max_y

        coords = np.array([[min_x, max_x, max_x, min_x],
                           [min_y, min_y, max_y, max_y]],
                          dtype=np.float)
        coords = coords.transpose()
        poly = Polygon(xy=coords, closed=True,
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
                x=self.centre_x, y=self.centre_y, text=self.value_text_unset,
                verticalalignment='center', horizontalalignment='center',
                fontsize=30,
                **self.value_text_kwargs)
            self.ax.add_artist(txt)
            self.els['value_text'] = txt

    def input(self, device, seq_time, signal):
        if signal.state != 0:
            # Start a capture animation.
            self.animate = 'capture'
            self.anim_start = seq_time
            self.anim_duration = self.dev._t_d2c
            self.anim_end = self.anim_start + self.anim_duration
            self.els['value_text'].set_text(str(signal.state))
            self.els['value_text'].set_fontproperties(
                FontProperties(style='italic', weight='bold'))
            self.els['value_text'].set_y(self.upper_y)

    def clr(self, device, seq_time, signal):
        # Start a clear-content animation.
        self.animate = 'clear'
        self.anim_start = seq_time
        self.anim_duration = self.dev._t_d2c
        self.anim_end = seq_time + self.anim_duration
        self.x_wobble_phases = 12 # out+back 3 times in each direction
        self.x_wobble_phase_time = self.anim_duration / self.x_wobble_phases
        self.els['value_text'].set_text('--XXX--')
        self.els['value_text'].set_fontproperties(FontProperties(style='italic'))
        self.els['value_text'].set_color('red')

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
                    FontProperties(style='normal', weight='normal'))
                self.animate = None
        elif self.animate == 'clear':
            if seq_time < self.anim_end:
                fract = self._phase_to_fract(seq_time)
                x_at = (self.centre_x - self.min_hw + 
                        fract * 0.5 * self.min_hw)
                self.els['value_text'].set_x(x_at)
            else:
                # Restore 'normality' + stop animation
                self.els['value_text'].set_x(self.centre_x)
                self.els['value_text'].set_text('---')
                self.els['value_text'].set_color('black')
                self.els['value_text'].set_fontproperties(
                    FontProperties(style='normal', weight='normal'))
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

