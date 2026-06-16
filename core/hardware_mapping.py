import json
import os
from enum import IntEnum

# Default paths
CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODBUS_CONFIG_PATH = os.path.join(CONFIG_DIR, "configs", "modbus_config.json")

# Default values to fallback on if loading fails or file doesn't exist
DEFAULT_COILS = {
    "SCR_COIL_ADDR": 0x01,
    "ACB_COIL_ADDR": 0x02,
    "CONTACTOR_100mA_LOAD_BANK_COIL_ADDR": 0x03,
    "CONTACTOR_120A_LOAD_BANK_COIL_ADDR": 0x04,
    "FCMC_TEST_START": 0x05,
    "SCCC_TEST_START": 0x06,
    "FCMCT_ACK": 0x07,
    "PRE_FUSING_MODE_COIL_ADDR": 0x08,
    "FAULT_INDICATION_BUZZER_COIL_ADDR": 0x09,
    "INPUT_STATUS_REQUEST": 0x10,
    "ACB_STATUS": 0x11,
    "CONTACTOR_100mA_STATUS": 0x12,
    "CONTACTOR_120A_STATUS": 0x13
}

DEFAULT_REGISTERS = {
    "VOLTAGE": 40001,
    "CURRENT": 40003,
    "PF": 40005,
    # Backward compatibility aliases
    "VOLTAGE_L1": 40001,
    "CURRENT_L1": 40003,
    "ACTIVE_POWER": 40005
}

MFM_FUNCTION_CODE = 4
MFM_REGISTER_TYPES = {
    "VOLTAGE": "SWAPPED_FLOAT",
    "CURRENT": "SWAPPED_FLOAT",
    "PF": "SWAPPED_FLOAT",
    "VOLTAGE_L1": "SWAPPED_FLOAT",
    "CURRENT_L1": "SWAPPED_FLOAT",
    "ACTIVE_POWER": "SWAPPED_FLOAT"
}

def load_modbus_config_from_file():
    global MFM_FUNCTION_CODE, MFM_REGISTER_TYPES
    coils = DEFAULT_COILS.copy()
    regs = DEFAULT_REGISTERS.copy()
    if os.path.exists(MODBUS_CONFIG_PATH):
        try:
            with open(MODBUS_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                if "plc_coils" in data:
                    coils = {k: int(v) for k, v in data["plc_coils"].items()}
                if "mfm_meter" in data:
                    if "connection" in data["mfm_meter"]:
                        MFM_FUNCTION_CODE = int(data["mfm_meter"]["connection"].get("function_code", 4))
                    if "registers" in data["mfm_meter"]:
                        for k, v in data["mfm_meter"]["registers"].items():
                            if isinstance(v, dict):
                                addr = v.get("address", 0)
                                regs[k] = int(addr)
                                reg_type = v.get("type", "SWAPPED_FLOAT")
                                MFM_REGISTER_TYPES[k] = reg_type
                            else:
                                regs[k] = int(v)
                                MFM_REGISTER_TYPES[k] = "SWAPPED_FLOAT"
                        # Sync compatibility aliases to latest loaded names
                        if "VOLTAGE" in regs:
                            regs["VOLTAGE_L1"] = regs["VOLTAGE"]
                            MFM_REGISTER_TYPES["VOLTAGE_L1"] = MFM_REGISTER_TYPES["VOLTAGE"]
                        if "CURRENT" in regs:
                            regs["CURRENT_L1"] = regs["CURRENT"]
                            MFM_REGISTER_TYPES["CURRENT_L1"] = MFM_REGISTER_TYPES["CURRENT"]
                        if "PF" in regs:
                            regs["ACTIVE_POWER"] = regs["PF"]
                            MFM_REGISTER_TYPES["ACTIVE_POWER"] = MFM_REGISTER_TYPES["PF"]
        except Exception as e:
            print(f"Error reading modbus_config.json: {e}")
    return coils, regs

coils_dict, regs_dict = load_modbus_config_from_file()

# Dynamically construct IntEnum
PLCCoil = IntEnum('PLCCoil', coils_dict)
MFMRegister = IntEnum('MFMRegister', regs_dict)

def reload_mappings():
    """Reloads modbus_config.json dynamically and updates the PLCCoil and MFMRegister globals."""
    global PLCCoil, MFMRegister, MFM_REGISTER_TYPES
    coils_dict, regs_dict = load_modbus_config_from_file()
    PLCCoil = IntEnum('PLCCoil', coils_dict)
    MFMRegister = IntEnum('MFMRegister', regs_dict)

