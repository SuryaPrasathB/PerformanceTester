import json
import os
from enum import IntEnum

# Default paths
CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODBUS_CONFIG_PATH = os.path.join(CONFIG_DIR, "configs", "modbus_config.json")

# Default values to fallback on if loading fails or file doesn't exist
DEFAULT_COILS = {
    "FCMC_TEST_START": 0x00,
    "SCCC_TEST_START": 0x01,
    "FCMCT_ACK": 0x02,
    "ACB_COIL_ADDR": 0x03,
    "SCR_COIL_ADDR": 0x04,
    "PRE_FUSING_MODE_COIL_ADDR": 0x05,
    "PROS_CT_TEST_START": 0x06
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

def load_modbus_config_from_file():
    coils = DEFAULT_COILS.copy()
    regs = DEFAULT_REGISTERS.copy()
    if os.path.exists(MODBUS_CONFIG_PATH):
        try:
            with open(MODBUS_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                if "plc_coils" in data:
                    coils = {k: int(v) for k, v in data["plc_coils"].items()}
                if "mfm_meter" in data and "registers" in data["mfm_meter"]:
                    for k, v in data["mfm_meter"]["registers"].items():
                        addr = v["address"] if isinstance(v, dict) and "address" in v else v
                        regs[k] = int(addr)
                    # Sync compatibility aliases to latest loaded names
                    if "VOLTAGE" in regs:
                        regs["VOLTAGE_L1"] = regs["VOLTAGE"]
                    if "CURRENT" in regs:
                        regs["CURRENT_L1"] = regs["CURRENT"]
                    if "PF" in regs:
                        regs["ACTIVE_POWER"] = regs["PF"]
        except Exception as e:
            print(f"Error reading modbus_config.json: {e}")
    return coils, regs

coils_dict, regs_dict = load_modbus_config_from_file()

# Dynamically construct IntEnum
PLCCoil = IntEnum('PLCCoil', coils_dict)
MFMRegister = IntEnum('MFMRegister', regs_dict)

def reload_mappings():
    """Reloads modbus_config.json dynamically and updates the PLCCoil and MFMRegister globals."""
    global PLCCoil, MFMRegister
    coils_dict, regs_dict = load_modbus_config_from_file()
    PLCCoil = IntEnum('PLCCoil', coils_dict)
    MFMRegister = IntEnum('MFMRegister', regs_dict)

