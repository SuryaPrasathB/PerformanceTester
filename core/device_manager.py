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
    # Signal emitted with aggregate HW status summary (status_text, is_all_ok)
    hw_status_summary = Signal(str, bool)

    def __init__(self, config_service, logger: logging.Logger, database_service=None):
        super().__init__()
        self.config_service = config_service
        self.logger = logger
        self.database_service = database_service
        
        self.devices: Dict[str, DeviceModel] = {}
        self.drivers: Dict[str, BaseDriver] = {}
        self.threads: Dict[str, QThread] = {}
        self.workers: Dict[str, DeviceWorker] = {}
        self.connection_states: Dict[str, bool] = {}  # Track per-device connection status
        
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
        elif model.type.lower() == "picoscope":
            from drivers.picoscope_driver import PicoScopeDriver
            return PicoScopeDriver(config_with_mock, self.logger)
        else:
            self.logger.error(f"Unknown device type: {model.type}")
            return None

    def _setup_device_thread(self, device_name: str, driver: BaseDriver):
        """Sets up a QThread and worker for a device's asynchronous operations."""
        if device_name in self.threads:
            self.logger.warning(f"Device thread for '{device_name}' already exists. Safely stopping existing thread...")
            old_thread = self.threads.pop(device_name, None)
            old_worker = self.workers.pop(device_name, None)
            if old_thread:
                if old_thread.isRunning():
                    old_thread.quit()
                    old_thread.wait()
                old_thread.deleteLater()
            if old_worker:
                old_worker.deleteLater()

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
        # Reset states and emit 'connecting' status
        for device_name in self.workers:
            self.connection_states[device_name] = False
        self.hw_status_summary.emit("Connecting...", False)
        
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
        self.connection_states[device_name] = success
        self.device_status_changed.emit(device_name, success)
        
        # Emit aggregate summary
        summary, all_ok = self._get_connection_summary()
        self.hw_status_summary.emit(summary, all_ok)

    def _get_connection_summary(self):
        """Returns (summary_text, is_all_ok) based on tracked connection states."""
        if not self.connection_states:
            return "No Devices", False
        
        total = len(self.connection_states)
        connected = sum(1 for v in self.connection_states.values() if v)
        failed_devices = [name for name, ok in self.connection_states.items() if not ok]
        
        if connected == total:
            return f"All OK ({connected}/{total})", True
        elif connected == 0:
            return f"All Failed ({total} devices)", False
        else:
            # Show first failed device name for quick identification
            short_failed = failed_devices[0].replace('1', '') if failed_devices else '?'
            if len(failed_devices) > 1:
                short_failed += f" +{len(failed_devices)-1}"
            return f"{connected}/{total} OK — {short_failed} failed", False

    def cleanup(self):
        """Cleans up threads before application exit."""
        self.disconnect_all()
        for device_name, thread in self.threads.items():
            thread.quit()
            thread.wait()

    def switch_device_type(self, device_name: str, new_type: str) -> bool:
        """
        Dynamically changes the device driver type (e.g. DLMS <-> Serial)
        and restarts the worker thread for that device.
        """
        if device_name not in self.devices:
            self.logger.error(f"Cannot switch device type: '{device_name}' not found.")
            return False
            
        model = self.devices[device_name]
        if model.type.lower() == new_type.lower():
            return True # Already correct type
            
        self.logger.info(f"Switching device '{device_name}' type from '{model.type}' to '{new_type}'...")
        
        # 1. Stop existing worker/thread
        if device_name in self.threads:
            worker = self.workers[device_name]
            thread = self.threads[device_name]
            
            # Disconnect slot synchronously (Blocking)
            from PySide6.QtCore import QMetaObject, Qt
            try:
                QMetaObject.invokeMethod(worker, "disconnect_device", Qt.BlockingQueuedConnection)
            except Exception as e:
                self.logger.warning(f"Error disconnecting '{device_name}' during switch: {e}")
                
            thread.quit()
            thread.wait()
            
            worker.deleteLater()
            thread.deleteLater()
            
        # 2. Update model type
        model.type = new_type
        
        # 3. Create new driver
        driver = self._create_driver(model)
        if not driver:
            self.logger.error(f"Failed to create new driver of type '{new_type}' for '{device_name}'.")
            return False
            
        self.drivers[device_name] = driver
        
        # 4. Restart thread & worker
        self._setup_device_thread(device_name, driver)
        
        # 5. Connect the new driver asynchronously
        worker = self.workers[device_name]
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(worker, "connect_device", Qt.QueuedConnection)
        
        return True

    def reload_devices(self):
        """Dynamically reloads devices and their drivers from the current configuration."""
        self.logger.info("Dynamically reloading hardware configurations...")
        
        # Disconnect and stop all current threads safely
        for device_name, worker in self.workers.items():
            from PySide6.QtCore import QMetaObject, Qt
            # We use QueuedConnection and allow them to finish naturally, or Blocking if needed.
            # Using BlockingQueuedConnection ensures it disconnects before thread quits.
            try:
                QMetaObject.invokeMethod(worker, "disconnect_device", Qt.BlockingQueuedConnection)
            except Exception as e:
                self.logger.warning(f"Error disconnecting {device_name} during reload: {e}")
                
        for device_name, thread in self.threads.items():
            thread.quit()
            thread.wait()
            
        self.devices.clear()
        self.drivers.clear()
        self.threads.clear()
        self.workers.clear()
        
        self._initialize_devices()
        self.logger.info("Hardware configurations reloaded successfully.")
