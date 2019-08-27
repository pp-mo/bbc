# code testing for the ball bearing computer

# instruction register makeup  : bit constants
IR_CLA = 0b10000000  # pre-clear acc at start of operation
IR_K2M = 0b01000000  # send K to address ram(for read/write)
IR_K2A = 0b00100000  # when not K2M : send K to A (Ax=[M]) / not P (JMP)
IR_M2A = 0b00010000  # (=M2M, =~A2M) : send M to A, rather than A to M
IR_CLC = 0b00001000  # [=C2A] pre-clear carry AND add C to A (ACx) / not P (SKC)
IR_ADC = 0b00000100  # add carry to A (ACx) or P (SKC)
IR_XTG = 0b00000010  # disable toggle for OR not ADD
IR_XCY = 0b00000001  # disable carry for XOR not ADD

# instruction codes {name: ir-bits}
INSTRUCTION_CODE_REGISTERS = {
    'STM': IR_K2M,
    'LDM': IR_K2M + IR_M2A + IR_CLA,
    'ADM': IR_K2M + IR_M2A + IR_CLC,
    'ACM': IR_K2M + IR_M2A + IR_CLC + IR_ADC,
    'XRM': IR_K2M + IR_M2A + IR_XCY,
    'ORM': IR_K2M + IR_M2A + IR_XCY + IR_XTG,
    'LDI': IR_M2A + IR_CLA + IR_K2A,
    'ADI': IR_M2A + IR_K2A + IR_CLC,
    'ACI': IR_M2A + IR_K2A + IR_CLC + IR_ADC,
    'XRI': IR_M2A + IR_K2A + IR_CLC + IR_ADC + IR_XCY,
    'ORI': IR_M2A + IR_K2A + IR_CLC + IR_ADC + IR_XCY + IR_XTG,
    'JMP': IR_M2A,
    'SKC': IR_M2A + IR_ADC
}

# function to build a single instruction for the code table
# code format:
# *(instruction_name,  instruction_it_bits, instruction_k_value)
def instruction(code, k=0):
    """
    Build a single instruction entry for the code table.

    Args:

    * code (string):
        name of an instruction (a key in INSTRUCTION_CODE_REGISTERS)
    * k (int):
        instruction address / constant value

    Returns:
        (code, ir-bits, k)
        This is the instruction table format.

    """
    return (code, INSTRUCTION_CODE_REGISTERS[code], k)


# The main runnable code table.
code = [
    instruction('LDI', 5),  # 00
    instruction('STM', 1),  # 01
    instruction('LDI', 3),  # 02
    instruction('STM', 2),  # 03
    instruction('LDM', 1),  # 04: "LOOP"
    instruction('ACM', 2),  # 05
    instruction('STM', 2),  # 06
    instruction('LDM', 3),  # 07
    instruction('ADI', -1),  # 08
    instruction('STM', 3),  # 09
    instruction('SKC'), # 10: skips while {3} > 0
    instruction('JMP', -1),  # 11: endless loop = STOP !
    instruction('JMP', -9)   # 12:  (13 - 9 = 4): back to "LOOP"
]
