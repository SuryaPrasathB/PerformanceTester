import sys
import os
import logging
import struct

# Set up logging to stdout
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymodbus.client import ModbusSerialClient

def test_mfm():
    port = "COM6"
    baud = 9600
    bytesize = 8
    parity = "N"
    stopbits = 1
    timeout = 1.0
    
    print(f"Connecting to Modbus RTU on {port} (Baud: {baud}, Parity: {parity}, Stopbits: {stopbits})...")
    client = ModbusSerialClient(
        port=port,
        baudrate=baud,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        timeout=timeout
    )
    
    connected = client.connect()
    if not connected:
        print("Failed to connect to serial port.")
        return
        
    print("Connected successfully.")
    
    # Try reading from Slave 1 and Slave 2
    for slave in [1, 2]:
        print(f"\n--- Testing Slave {slave} ---")
        
        # Test Function Code 3 (Holding Registers)
        print("Trying Function Code 3 (Read Holding Registers) at address 0 (offset of 40001)...")
        try:
            res_fc3 = client.read_holding_registers(address=0, count=2, slave=slave)
            if res_fc3.isError():
                print(f"FC3 Error: {res_fc3}")
            else:
                regs = res_fc3.registers
                print(f"FC3 Success: Registers = {regs}")
                # Try decoding float
                packed = struct.pack('>HH', regs[1], regs[0])
                val = struct.unpack('>f', packed)[0]
                print(f"FC3 Swapped Float value: {val}")
                packed_unswapped = struct.pack('>HH', regs[0], regs[1])
                val_unswapped = struct.unpack('>f', packed_unswapped)[0]
                print(f"FC3 Unswapped Float value: {val_unswapped}")
        except Exception as e:
            print(f"FC3 Exception: {e}")
            
        # Test Function Code 4 (Input Registers)
        print("Trying Function Code 4 (Read Input Registers) at address 0 (offset of 40001)...")
        try:
            res_fc4 = client.read_input_registers(address=0, count=2, slave=slave)
            if res_fc4.isError():
                print(f"FC4 Error: {res_fc4}")
            else:
                regs = res_fc4.registers
                print(f"FC4 Success: Registers = {regs}")
                packed = struct.pack('>HH', regs[1], regs[0])
                val = struct.unpack('>f', packed)[0]
                print(f"FC4 Swapped Float value: {val}")
                packed_unswapped = struct.pack('>HH', regs[0], regs[1])
                val_unswapped = struct.unpack('>f', packed_unswapped)[0]
                print(f"FC4 Unswapped Float value: {val_unswapped}")
        except Exception as e:
            print(f"FC4 Exception: {e}")

    client.close()

if __name__ == "__main__":
    test_mfm()
