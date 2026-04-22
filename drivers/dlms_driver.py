from .base_driver import BaseDriver
import logging
import time
from typing import Optional

# Gurux imports
from gurux_dlms.secure import GXDLMSSecureClient
from gurux_dlms.enums import InterfaceType, Authentication, Security, Standard
from gurux_dlms.objects.enums.SecuritySuite import SecuritySuite
from gurux_dlms.objects import GXDLMSData
from gurux_net import GXNet
from gurux_serial import GXSerial

# Wrapper imports
from .gurux.GXSettings import GXSettings
from .gurux.GXDLMSReader import GXDLMSReader

class DlmsDriver(BaseDriver):
    """
    DLMS Driver using gurux-dlms.
    Supports both Serial and TCP/IP connections.
    """
    def __init__(self, config: dict, logger: logging.Logger):
        super().__init__(config, logger)
        
        self.connection_type = config.get("connection_type", "serial").lower()
        self.port = config.get("port", "COM1")
        self.baudrate = config.get("baudrate", 9600)
        self.ip_address = config.get("ip_address", "127.0.0.1")
        self.tcp_port = config.get("tcp_port", 4059)
        self.timeout = config.get("timeout", 30)

        # DLMS Configuration
        self.client_address = config.get("client_address", 48)
        self.server_address = config.get("server_address", 1)
        self.password = config.get("password", b"12345678ABCDEFGH")
        if isinstance(self.password, str):
            self.password = self.password.encode('ascii')
            
        self.system_title = config.get("system_title", b"UPS00001")
        if isinstance(self.system_title, str):
            self.system_title = self.system_title.encode('ascii')
            
        self.auth_key = config.get("authentication_key", b"1111111111111111")
        if isinstance(self.auth_key, str):
            self.auth_key = self.auth_key.encode('ascii')
            
        self.block_cipher_key = config.get("block_cipher_key", b"1111111111111111")
        if isinstance(self.block_cipher_key, str):
            self.block_cipher_key = self.block_cipher_key.encode('ascii')

        self.media = None
        self.client = None
        self.reader = None
        self.settings = None

    def connect(self) -> bool:
        """Establishes DLMS connection."""
        if self.mock_mode:
            self.logger.info(f"[MOCK] DLMS connected via {self.port} (type: {self.connection_type}).")
            self.is_connected = True
            return True

        try:
            self.logger.info(f"DLMS Driver: Attempting to connect (type: {self.connection_type})...")
            
            # Setup media
            if self.connection_type == "tcp":
                self.media = GXNet()
                self.media.hostName = self.ip_address
                self.media.port = self.tcp_port
                self.media.timeout = self.timeout
            else:
                self.media = GXSerial(self.port)
                self.media.port = self.port
                self.media.baudRate = self.baudrate
                self.media.timeout = self.timeout

            # Setup client
            self.client = GXDLMSSecureClient(True)
            self.client.useLogicalNameReferencing = True
            self.client.interfaceType = InterfaceType.WRAPPER

            self.client.clientAddress = self.client_address
            self.client.serverAddress = self.server_address
            self.client.authentication = Authentication.HIGH
            self.client.password = self.password

            self.client.ciphering.systemTitle = self.system_title
            self.client.ciphering.securitySuite = SecuritySuite.SUITE_0
            self.client.ciphering.authenticationKey = self.auth_key
            self.client.ciphering.blockCipherKey = self.block_cipher_key

            self.client.ciphering.security = Security.AUTHENTICATION_ENCRYPTION
            self.client.standard = Standard.INDIA

            # Setup settings
            self.settings = GXSettings()
            self.settings.media = self.media
            self.settings.client = self.client
            self.settings.trace = False

            # Open media
            self.media.open()
            
            # Initialize reader
            self.reader = GXDLMSReader(self.client, self.media, False, 0)
            self.reader.initializeConnection()
            
            self.is_connected = True
            self.logger.info("DLMS Driver: Successfully connected.")
            return True

        except Exception as e:
            self.logger.error(f"DLMS connection failed: {str(e)}")
            self.is_connected = False
            return False

    def disconnect(self) -> bool:
        """Closes the DLMS connection."""
        if self.mock_mode:
            self.logger.info(f"[MOCK] DLMS disconnected.")
            self.is_connected = False
            return True

        try:
            if self.media:
                self.logger.info("DLMS Driver: Disconnecting...")
                if self.reader:
                    try:
                        self.reader.close()
                    except Exception as e:
                        self.logger.warning(f"Error closing reader: {e}")
                self.media.close()
            self.is_connected = False
            self.logger.info("DLMS Driver: Successfully disconnected.")
            return True
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
            return False

    def read_data(self, obis_code: str = "1.0.0.0.0.255") -> any:
        """Reads data from the DLMS meter using an OBIS code."""
        if self.mock_mode:
            self.logger.debug(f"[MOCK] DLMS reading OBIS {obis_code}.")
            time.sleep(0.1)
            return "MOCK_DLMS_VALUE"

        if not self.is_connected or not self.reader:
            self.logger.error("DLMS Driver: Cannot read data, not connected.")
            return None

        try:
            self.logger.debug(f"DLMS Driver: Reading OBIS {obis_code}...")
            obj = GXDLMSData(obis_code)
            # 2 stands for value attribute
            value = self.reader.read(obj, 2)
            self.logger.debug(f"DLMS Driver: Read value {value} from OBIS {obis_code}.")
            
            # Try to decode if it's bytes
            if isinstance(value, bytes):
                try:
                    value = value.decode("ascii", errors="ignore").strip("\x00 ")
                except:
                    pass
            return value
            
        except Exception as e:
            self.logger.error(f"DLMS Driver: Error reading OBIS {obis_code}: {e}")
            return None

    def write_data(self, obis_code: str, value: any) -> bool:
        """Writes data to the DLMS meter."""
        if self.mock_mode:
            self.logger.debug(f"[MOCK] DLMS writing {value} to OBIS {obis_code}.")
            time.sleep(0.1)
            return True

        if not self.is_connected or not self.reader:
            self.logger.error("DLMS Driver: Cannot write data, not connected.")
            return False

        try:
            self.logger.debug(f"DLMS Driver: Writing {value} to OBIS {obis_code}...")
            obj = GXDLMSData(obis_code)
            # Setting the value attribute
            obj.value = value
            self.reader.write(obj, 2)
            self.logger.debug(f"DLMS Driver: Successfully wrote to OBIS {obis_code}.")
            return True
            
        except Exception as e:
            self.logger.error(f"DLMS Driver: Error writing to OBIS {obis_code}: {e}")
            return False

    def poll(self, obis_codes: list) -> dict:
        """Polls multiple OBIS codes."""
        if self.mock_mode:
            self.logger.debug(f"[MOCK] DLMS polling OBIS codes {obis_codes}.")
            time.sleep(0.1)
            return {code: "MOCK_POLL_VALUE" for code in obis_codes}

        results = {}
        for code in obis_codes:
            results[code] = self.read_data(code)
        return results

