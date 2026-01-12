import sys

sys.path.append(
    '/storage/emulated/0/qpython/')

from sim.tests import \
    okeq, okin, setsig, fails

from sim.signal import Signal
from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.device.pulse_rom import PulseRom

words = [17, 4, 0, 42, 299]
rom = PulseRom(
    name='pm',
    rom_words=words,
    t_addr_2_asel=1.0,
    t_asel_2_read=1.0,
    t_read_2_aclr=1.0,
    t_aclr_2_addr=1.0,
    t_out_delay=10.0)

print(rom)

addr = Signal('addr')
aen = Signal('!a_ena')
aclr = Signal('!a_dis')
read = Signal('!read')
rom.connect('addr', addr)
rom.connect('x_asel', aen)
rom.connect('x_aclr', aclr)
rom.connect('x_read', read)

addr.trace()
aen.trace()
aclr.trace()
read.trace()
rom.out.trace()

print('\ncheck set, clr, set')
SEQ.addall([
    setsig(100.0, addr, 3),
    setsig(110.0, aen, '!'),
    setsig(115.0, read, '!'),
    setsig(120.0, aclr, '!'),

    setsig(200.0, addr, 1),
    setsig(210.0, aen, '!'),
    setsig(215.0, read, '!'),
    setsig(220.0, aclr, '!'),
])
SEQ.run(150.)
okeq(rom.out.state, 42)
SEQ.run()
okeq(rom.out.state, 4)
