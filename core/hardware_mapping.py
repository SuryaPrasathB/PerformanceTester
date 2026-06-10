from enum import IntEnum

class PLCCoil(IntEnum):
    FCMC_TEST_START              = 0x00
    SCCC_TEST_START              = 0x01
    FCMCT_ACK                    = 0x02
    ACB_COIL_ADDR                = 0x03
    SCR_COIL_ADDR                = 0x04
    PRE_FUSING_MODE_COIL_ADDR    = 0x05
    PROS_CT_TEST_START           = 0x06

class MFMRegister(IntEnum):
    # Dummy registers for now
    VOLTAGE_L1 = 0x0100
    CURRENT_L1 = 0x0101
    ACTIVE_POWER = 0x0102
