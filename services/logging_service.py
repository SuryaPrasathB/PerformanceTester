import logging
import os
from PySide6.QtCore import QObject, Signal

class QtLogEmitter(QObject):
    """
    QObject to emit signals for new log messages.
    Needs to be a QObject to use Qt signals.
    """
    log_message = Signal(str, str) # level, message

class QtLogHandler(logging.Handler):
    """
    Custom logging handler that emits a Qt signal for each log record.
    """
    def __init__(self, emitter: QtLogEmitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record):
        try:
            msg = self.format(record)
            self.emitter.log_message.emit(record.levelname, msg)
        except Exception:
            self.handleError(record)

class LoggingService:
    """
    LoggingService configures and provides access to the application logger.
    """
    def __init__(self, log_dir: str = "logs", log_file: str = "app.log"):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, log_file)
        self.emitter = QtLogEmitter()
        self._setup_logger()

    def _setup_logger(self):
        """Configures the root logger with file, console, and Qt handlers."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Get the root logger
        self.logger = logging.getLogger("EnergyMeterApp")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent adding handlers multiple times if instantiated again
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # File Handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Qt Handler
        qt_handler = QtLogHandler(self.emitter)
        qt_handler.setLevel(logging.INFO) # Broadcast INFO and above to UI
        qt_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(qt_handler)

    def get_logger(self):
        """Returns the configured logger."""
        return self.logger
        
    def get_emitter(self):
        """Returns the Qt emitter to connect UI slots to log signals."""
        return self.emitter
