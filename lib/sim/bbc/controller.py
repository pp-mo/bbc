# Main instruction cycle controller

from sim.signal import SIG_UNDEF
from sim.device import Device, Action

class BbcController(Device):
    phase_names_and_default_durations = [
        ('p0_Next', 4.0),
        ('p1_AddressPm', 2.5),
        ('p2_PmFetchIr', 12.0),
        ('p3_PmFetchK_Clc', 20.0),
        ('p4_DmAddr', 10.0),
        ('p5_AddC_SaveA', 10.0),
    ]
    def __init__(self, name='bbc', *args, **kwargs):
        self.n_phases = len(self.phase_names_and_default_durations)
        self.phase_durations = []
        for i_phase, (phase_name, t_phase) in enumerate(self.phase_names_and_default_durations):
            timekey_indexname = 't_' + str(i_phase)
            timekey_phasename = 't_' + phase_name
            duration_given = kwargs.pop(timekey_indexname, None) or kwargs.pop(timekey_phasename, None)
            if duration_given is not None:
                t_phase = float(duration_given)
            self.phase_durations.append(t_phase)

        # do super-init
        super(BbcController, self).__init__(name, *args, **kwargs)
        # add outputs : a phase-name, and an event output for each phase
        self.add_output('current_phase', SIG_UNDEF)
        for phase_name, _ in self.phase_names_and_default_durations:
            self.add_output(phase_name)
        self.reset()

    def reset(self):
        self.i_next_phase = 0

    @Device.input
    def start(self, time, signal):
        self.seq.add((time, Action(self, '_do_phase')))

    @Device.action
    def _do_phase(self, time):
        i_this_phase = self.i_next_phase
        self.i_next_phase = (self.i_next_phase + 1) % self.n_phases
        phase_name = self.phase_names_and_default_durations[i_this_phase][0]
        phase_duration = self.phase_durations[i_this_phase]
        self.current_phase.set(time, phase_name)
        getattr(self, phase_name).set(time, '!')
        return (time + phase_duration, Action(self, '_do_phase'))
