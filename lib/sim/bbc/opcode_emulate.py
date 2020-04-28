from collections import namedtuple

from sim.bbc.code import INSTRUCTION_CODE_REGISTERS as OPS

_VALID_OPCODES = OPS.keys()

CpuState = namedtuple('CpuState', ('ram', 'ir', 'acc', 'carry'))

def emulate_opcode(codename, k, cpustate):
    """
    Emulate one opcode.

    Accepts and returns a cpustate.

    """
    # Take a deep copy.
    cpustate = CpuState(cpustate.ram[:],
                        cpustate.ir, cpustate.acc, cpustate.carry)

    if codename.upper() not in _VALID_OPCODES:
        raise ValueError('Opcode "{}" not known.'.format(codename))

    codename = codename.lower()
    k = (k + 512) % 256
    n_ram = len(cpustate.ram)

    def check_k_is_valid_addr():
        if k < 0 or k >= n_ram:
            msg = 'Opcode {} @{:03d} : k={} outside size of ram, {}'
            raise ValueError(msg.format(codename, cpustate.ir, k, n_ram))

    assert len(codename) == 3
    memop = codename[2] == 'm'
    if memop:
        check_k_is_valid_addr()

    ir_next = (cpustate.ir + 1) % 256
    ram = cpustate.ram[:]  # N.B. a copy !
    acc = cpustate.acc
    carry = cpustate.carry

    if codename == 'stm':
        ram[k] = acc
        acc = 0  # NOTE THIS !!
    elif codename == 'ldm':
        acc = ram[k]
    elif codename == 'adm':
        acc = acc + ram[k]
    elif codename == 'acm':
        acc = acc + ram[k] + carry
    elif codename == 'orm':
        acc = acc | ram[k]
    elif codename == 'xrm':
        acc = acc ^ ram[k]
    elif codename == 'ldi':
        acc = k
    elif codename == 'adi':
        acc = acc + k
    elif codename == 'aci':
        acc = acc + k + carry
    elif codename == 'ori':
        acc = acc | k
    elif codename == 'xri':
        acc = acc ^ k
    elif codename == 'skc':
        if carry != 0:
            ir_next = ir_next + 1
    elif codename == 'jmp':
        ir_next = ir_next + k

    is_arith = codename in ('adm', 'acm', 'adi', 'aci')
    if is_arith:
        acc = (acc + 1024) % 512
        carry = 1 if acc >= 256 else 0

    acc = acc % 256
    ir_next = ir_next % 256
    cpustate = CpuState(ram=ram, ir=ir_next, acc=acc, carry=carry)
    return cpustate

