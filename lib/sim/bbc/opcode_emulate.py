from collections import namedtuple

from sim.bbc.code import INSTRUCTION_CODE_REGISTERS as _ALLOPS

_VALID_OPCODES = _ALLOPS.keys()

CpuState = namedtuple('CpuState', ('ram', 'ir', 'acc', 'carry'))

def emulate_opcode(codename, k, cpustate):
    """
    Emulate one opcode.

    Accepts and returns a CpuState.

    """
    if codename.upper() not in _VALID_OPCODES:
        raise ValueError('Opcode "{}" not known.'.format(codename))

    # Get the input data (including cpustate) in the forms that we want it.
    codename = codename.lower()
    k = (k + 512) % 256
    ram = cpustate.ram[:]  # N.B. must copy this !
    ir = cpustate.ir
    ir_next = (ir + 1) % 256
    acc = cpustate.acc
    carry = cpustate.carry
    n_ram = len(ram)

    def check_k_is_valid_addr():
        if k < 0 or k >= n_ram:
            msg = 'Opcode {} @{:03d} : k={} outside size of ram, {}'
            raise ValueError(msg.format(codename, ir, k, n_ram))

    assert len(codename) == 3
    opcode_is_memory_op = codename[2] == 'm'
    if opcode_is_memory_op:
        check_k_is_valid_addr()

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

    opcode_is_arithmetic = codename in ('adm', 'acm', 'adi', 'aci')
    if opcode_is_arithmetic:
        acc = (acc + 1024) % 512
        carry = 1 if acc >= 256 else 0

    acc = acc % 256
    ir_next = ir_next % 256
    new_cpustate = CpuState(ram=ram, ir=ir_next, acc=acc, carry=carry)
    return new_cpustate

