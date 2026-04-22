from PySide6.QtCore import QObject, QThread, Signal, Slot
import logging
from typing import Dict, Any

from models.device_model import DeviceModel
from drivers.base_driver import BaseDriver
from drivers.serial_driver import SerialDriver
from drivers.modbus_driver import ModbusDriver
from drivers.dlms_driver import DlmsDriver

class DeviceWorker(QObject):
    """
    Worker object for QThread. 
    Handles connection tasks without blocking the main UI thread.
    """
    connection_result = Signal(str, bool) # device_name, success

    def __init__(self, driver: BaseDriver, device_name: str):
        super().__init__()
        self.driver = driver
        self.device_name = device_name

    @Slot()
    def connect_device(self):
        """Attempts connection and emits the result."""
        success = self.driver.connect()
        self.connection_result.emit(self.device_name, success)

    @Slot()
    def disconnect_device(self):
        """Attempts disconnection and emits the result."""
        self.driver.disconnect()
        self.connection_result.emit(self.device_name, False)


class DeviceManager(QObject):
    """
    DeviceManager manages device configurations, dynamically instantiates 
    drivers, and handles non-blocking connections using QThreads.
    """
    # Signal emitted when a device's connection status changes
    device_status_changed = Signal(str, bool) 

    def __init__(self, config_service, logger: logging.Logger):
        super().__init__()
        self.config_service = config_service
        self.logger = logger
        
        self.devices: Dict[str, DeviceModel] = {}
        self.drivers: Dict[str, BaseDriver] = {}
        self.threads: Dict[str, QThread] = {}
        self.workers: Dict[str, DeviceWorker] = {}
        
        self._initialize_devices()

    def _initialize_devices(self):
        """Loads devices from config and instantiates corresponding drivers."""
        device_configs = self.config_service.get_devices()
        
        for dev_config in device_configs:
            model = DeviceModel.from_dict(dev_config)
            self.devices[model.name] = model
            
            driver = self._create_driver(model)
            if driver:
                self.drivers[model.name] = driver
                self._setup_device_thread(model.name, driver)
            else:
                self.logger.error(f"Failed to create driver for device {model.name} of type {model.type}.")

    def _create_driver(self, model: DeviceModel) -> BaseDriver:
        """Dynamically creates the appropriate driver based on device type."""
        config_with_mock = model.connection_details.copy()
        config_with_mock["mock"] = model.mock
        
        if model.type.lower() == "serial":
            return SerialDriver(config_with_mock, self.logger)
        elif model.type.lower() == "modbus":
            return ModbusDriver(config_with_mock, self.logger)
        elif model.type.lower() == "dlms":
            return DlmsDriver(config_with_mock, self.logger)
        else:
            self.logger.error(f"Unknown device type: {model.type}")
            return None

    def _setup_device_thread(self, device_name: str, driver: BaseDriver):
        """Sets up a QThread and worker for a device's asynchronous operations."""
        thread = QThread()
        worker = DeviceWorker(driver, device_name)
        
        worker.moveToThread(thread)
        
        # Connect worker signals to manager slots
        worker.connection_result.connect(self._on_connection_result)
        
        self.threads[device_name] = thread
        self.workers[device_name] = worker
        
        # Start the thread event loop
        thread.start()

    def connect_all(self):
        """Initiates connection for all managed devices."""
        for device_name, worker in self.workers.items():
            self.logger.info(f"Initiating connection for {device_name}...")
            # Use QMetaObject to safely invoke slot in the worker's thread
            from PySide6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(worker, "connect_device", Qt.QueuedConnection)

    def disconnect_all(self):
        """Initiates disconnection for all managed devices."""
        for device_name, worker in self.workers.items():
            self.logger.info(f"Initiating disconnection for {device_name}...")
            from PySide6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(worker, "disconnect_device", Qt.QueuedConnection)
            
    def get_devices(self) -> Dict[str, DeviceModel]:
        """Returns the dictionary of initialized device models."""
        return self.devices

    @Slot(str, bool)
    def _on_connection_result(self, device_name: str, success: bool):
        """Slot called when a worker finishes a connection attempt."""
        status = "Connected" if success else "Disconnected"
        self.logger.info(f"Device {device_name} status updated: {status}")
        self.device_status_changed.emit(device_name, success)

    def cleanup(self):
        """Cleans up threads before application exit."""
        self.disconnect_all()
        for device_name, thread in self.threads.items():
            thread.quit()
            thread.wait()
