import numpy as np
from matplotlib.patches import Polygon, Circle
from matplotlib.text import Text

from sim import SlotsHolder
from sim.view import DeviceView
from sim.device.pulse_rom import PulseRom


class PulseRomBitsView(DeviceView):
    target_devicetype = PulseRom

    def __init__(self, device, main_x_leftright, main_y_topbottom,
                 address_lhs_width_fract=0.12,
                 address_lhs_width_min=2.0,
                 main_outline_poly_kwargs=None,
                 value_text_kwargs=None):
        super(PulseLatchView, self).__init__(device)
        self.input_x, self.input_y = input_xy
        self.output_x, self.output_y = output_xy
        self.min_hh = min_halfheight
        self.min_hw = min_halfwidth
        self.outline_poly_kwargs = {'edgecolor':'red', 'linewidth':1.5}
        if outline_poly_kwargs:
            self.outline_poly_kwargs.update(outline_poly_kwargs)
        self.value_text_kwargs = {'fontsize':30}
        if value_text_kwargs:
            self.value_text_kwargs.update(value_text_kwargs)
        self.onebit_mode = onebit_mode
        self.onebit_circle_kwargs = {
            'facecolor':'blue', 'radius':4.0,
            'edgecolor':'black', 'linewidth':1.5}
        if onebit_circle_kwargs:
            self.onebit_circle_kwargs.update(onebit_circle_kwargs)
        self.hook_device_calls(('input', 'clr'))
        self.value_text_unset = '---'

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

    def ani_init(self, axes):
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
        self.box_poly = poly

        if self.onebit_mode:
            # Make a circle to show the 'blob'.
            circ = Circle(
                xy=(self.centre_x, self.centre_y),
                axes=self.ax, **self.onebit_circle_kwargs)
            self.ax.add_patch(circ)
            self.els['blob_circle'] = circ
        else:
            # Make a text to show the value.
            kwargs = {'fontsize':30}
            kwargs.update(self.value_text_kwargs)
            txt = Text(
                x=self.centre_x, y=self.centre_y, text=self.value_text_unset,
                verticalalignment='center', horizontalalignment='center',
                **self.value_text_kwargs)
            self.ax.add_artist(txt)
            self.value_text = txt

        # Setup self._anidata to contain all animation state information.
        AniData = SlotsHolder.newtype('pulselatch_anidata', ('value_text', 'blob_circle'))
        ValueTextData = SlotsHolder.newtype(
            'ValueTextData',
            ('position', 'text', 'color', 'fontstyle', 'fontweight'))
        self._anidata = AniData()
        self._anidata.value_text = self._get_element_state(
            self.value_text, ValueTextData)
        # Also require a dummy 'bloc_circle' object (for now, just testing)
        self.blob_circle = None
        self._anidata.blob_circle = SlotsHolder.newtype('DummyBlobCircleData', [])

    def _phase_to_fract(self, time):
        cycle = (time - self.anim_start) / self.x_wobble_phase_time
        fract = cycle % 1.0
        phase = int(np.floor(cycle % 4.0))
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

    def ani_updated_state(self, seq_time):
        """Return an updated animation state, or None if no change."""
        anim = self._anidata.copy()
        work_todo = self.animate != None  # Save for final check
        if self.animate == 'capture':
            if seq_time < self.anim_end:
                fract = (seq_time - self.anim_start) / self.anim_duration
                y_at = (self.upper_y +
                        fract * (self.centre_y - self.upper_y))
                anim.value_text.position = (anim.value_text.position[0], y_at)
            else:
                # Restore 'normality' + stop animation
                anim.value_text.position = (self.centre_x, self.centre_y)
                anim.value_text.fontstyle = 'normal'
                anim.value_text.fontweight = 'normal'
                self.animate = None
        elif self.animate == 'clear':
            if seq_time < self.anim_end:
                fract = self._phase_to_fract(seq_time)
                x_at = (self.centre_x + 0.2 * self.min_hw * fract)
                anim.value_text.position = (x_at, anim.value_text.position[1])
            else:
                # Restore 'normality' + stop animation
                anim.value_text.position = (self.centre_x, self.centre_y)
                anim.value_text.text = '---'
                anim.value_text.color = 'black'
                anim.value_text.fontstyle = 'normal'
                anim.value_text.fontweight = 'normal'
                self.animate = None

        return anim if work_todo else None

    def ani_apply_state(self, anim):
        # This looks like *standard* implementation ?
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

    def input(self, device, seq_time, signal):
        # Hook from device input method 'input' .
        if signal.state != 0:
            # Start a capture animation.
            self.animate = 'capture'
            self.anim_start = seq_time
            self.anim_duration = self.dev._t_delay
            self.anim_end = self.anim_start + self.anim_duration
            self.value_text.set_text(str(signal.state))
            self.value_text.set_fontstyle('italic')
            self.value_text.set_fontweight('bold')
            self.value_text.set_y(self.upper_y)

    def clr(self, device, seq_time, signal):
        # Hook from device input method 'clr' .
        self.value_text = self.value_text
        # Start a clear-content animation.
        self.animate = 'clear'
        self.anim_start = seq_time
        self.anim_duration = self.dev._t_delay
        self.anim_end = seq_time + self.anim_duration
        self.x_wobble_phases = 12 # out+back 3 times in each direction
        self.x_wobble_phase_time = self.anim_duration / self.x_wobble_phases
        self.value_text.set_text('--XXX--')
        self.value_text.set_fontstyle('italic')
        self.value_text.set_color('red')
