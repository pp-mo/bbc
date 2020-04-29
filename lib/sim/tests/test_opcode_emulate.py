from sim.bbc.opcode_emulate import CpuState, emulate_opcode
from six.moves import input

# Hailstone numbers calculation

NSHFT = 0
A = 1
T = 2
TOPBIT = 3
NSEQ = 4

pm = [
    ('ldi', 1),
    ('stm', NSEQ),
    # :GO
    ('ldi', -8),
    ('stm', NSHFT),
    ('ldm', A),
    ('stm', T),
    ('stm', TOPBIT),
    # :SHIFT
    ('ldm', T),
    ('adm', T ),
    ('orm', TOPBIT), # retrieve lower bit from previous *2
    ('stm', T),
    ('aci', 0),
    ('stm', TOPBIT),    # store A*2 carry in TOPBIT
    ('ldm', NSHFT),
    ('adi', 1),
    ('stm', NSHFT),
    ('skc', 0),
    ('jmp', -11),  # --> SHIFT
    ('ldm', TOPBIT),
    ('adi', -1),
    ('skc', 0),
    ('jmp', 6),  # --> EVE_div2
    ('ldm', A),
    ('adm', A),
    ('adm', A),
    ('adi', 1),
    ('stm', A),
    ('jmp', 6),  # --> COUNTUP
    # : EVE_div2
    ('ldm', T),
    ('stm', A),
    ('ldm', T),
    ('adi', -2),
    ('skc', 0),
    # : DONE
    ('jmp', -1),  # --> DONE
    # : COUNTUP
    ('ldm', NSEQ),
    ('adi', 1),
    ('stm', NSEQ),
    ('jmp', -36),  # --> GO
]


def emu(cpu, singlestep=False, break_step=None, break_addrs=[]):
    if break_step or break_addrs:
        singlestep = False
    step_fmt = '#{:04d} @{:04d}: {} {}'
    print('\nStart cpustate=\n  {}'.format(cpu))
    i_step = 0
    while True:
        i_step += 1
        opcode, k = pm[cpu.ir]
        print(step_fmt.format(
            i_step, cpu.ir, opcode.upper(), k))
        cpu = emulate_opcode(opcode, k, cpu)
        print('  {}'.format(cpu))
        print('    next @{} = {} {}'.format(
            cpu.ir, pm[cpu.ir][0], pm[cpu.ir][1]))
        if (singlestep
                or i_step == break_step
                or cpu.ir in break_addrs):
            if i_step == break_step or cpu.ir in break_addrs:
                print('\n <BREAK @{}>'.format(cpu.ir))
                # Always pause from a breakpoint..
                singlestep = True
            resp = input().strip().upper()
            if resp.startswith('Q'):
                print('\n<QUIT>\n')
                exit(0)
            elif len(resp) > 0 and resp[0].isdigit():
                # run ahead N steps if a number
                n_steps = int(resp)
                print('<steps = {}>'.format(n_steps))
                singlestep = False
                break_step = i_step + n_steps
            elif len(resp) > 0:
                # run on if nonempty
                print('<Running..>')
                singlestep = False
            else:
                # return to single stepping
                print('<Stepping..>')
                singlestep = True
        else:
            print('')

# Test sequence
RAM = [-111] * 16  # Spottable value for unused RAM locations.
RAM[A] = 3
cpu = CpuState(ram=RAM, ir=0, acc=0, carry=0)

do_singlestep = True
do_singlestep = False
# emu(cpu, do_singlestep, break_step=73)
emu(cpu, do_singlestep, break_addrs=[2, 33])  # break each result, and end
# emu(cpu, do_singlestep, break_addrs=[33])  # break at end only (--> length count)


# Python implementation for reference.
def hail(x):
    result = []
    while x > 1:
        result += [x]
        if x % 2 == 0:
            x = x // 2
        else:
            x = 3 * x + 1
    return result

def showlens():
    i = 1
    while True:
        i = i+1
        h = hail(i)
        n = len(h)
        m = max(h)
        print(i, n, m)
        if m > 255:
            break

    # Results:
    #     2 1 2
    #     3 7 16
    #     4 2 4
    #     5 5 16
    #     6 8 16
    #     7 16 52
    #     8 3 8
    #     9 19 52
    #     10 6 16
    #     11 14 52
    #     12 9 16
    #     13 9 40
    #     14 17 52
    #     15 17 160
    #     16 4 16
    #     17 12 52
    #     18 20 52
    #     19 20 88
    #     20 7 20
    #     21 7 64
    #     22 15 52
    #     23 15 160
    #     24 10 24
    #     25 23 88
    #     26 10 40
    #     27 111 9232

