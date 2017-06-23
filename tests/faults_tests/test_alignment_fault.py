import pytest
from armulator.arm_v6 import ArmV6
from armulator.memory_controller_hub import MemoryController
from bitstring import BitArray
from armulator.memory_types import RAM
from armulator.opcodes.thumb_instruction_set.thumb_instruction_set_encoding_16_bit.ldm_thumb_t1 import LdmThumbT1
from armulator.arm_exceptions import DataAbortException


def test_ldm_alignment_fault():
    arm = ArmV6()
    arm.take_reset()
    instr = BitArray(bin="1100100100100100")
    arm.registers.drsrs[0].set_en(True)  # enabling memory region
    arm.registers.drsrs[0].set_rsize("0b01000")  # setting region size
    arm.registers.drbars[0] = BitArray(hex="0x0F000000")  # setting region base address
    arm.registers.dracrs[0].set_ap("0b011")  # setting access permissions
    arm.registers.mpuir.set_iregion("0x01")  # declaring the region
    arm.registers.mpuir.set_dregion("0x01")  # declaring the region
    arm.registers.sctlr.set_u(True)
    ram_memory = RAM(0x100)
    mc = MemoryController(ram_memory, 0x0F000000, 0x0F000100)
    arm.mem.memories.append(mc)
    opcode = arm.decode_instruction(instr)
    opcode = opcode.from_bitarray(instr, arm)
    assert type(opcode) == LdmThumbT1
    assert opcode.wback is False
    assert opcode.n == 1
    assert opcode.registers == "0b0000000000100100"
    arm.registers.set(opcode.n, BitArray(hex="0x0F000003"))
    with pytest.raises(DataAbortException) as dabort_exception:
        arm.execute_instruction(opcode)
    assert dabort_exception.value.is_alignment_fault()
    assert not dabort_exception.value.second_stage_abort()
    arm.registers.take_data_abort_exception(dabort_exception.value)
    assert arm.registers.get_pc() == "0x00000014"
