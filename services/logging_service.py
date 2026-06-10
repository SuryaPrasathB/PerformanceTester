import logging
import os
from datetime import datetime, timedelta
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
    def __init__(self, base_log_dir: str = "logs"):
        self.base_log_dir = base_log_dir
        self._cleanup_old_logs(days=31)
        
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        
        self.log_dir = os.path.join(self.base_log_dir, date_str)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        self.log_file = os.path.join(self.log_dir, f"{time_str}.log")
        self.emitter = QtLogEmitter()
        self._setup_logger()
        
    def _cleanup_old_logs(self, days=31):
        """Deletes log folders older than the specified number of days."""
        if not os.path.exists(self.base_log_dir):
            return

        now = datetime.now()
        cutoff_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)
        
        for item in os.listdir(self.base_log_dir):
            item_path = os.path.join(self.base_log_dir, item)
            if os.path.isdir(item_path):
                try:
                    # Check if folder matches YYYY-MM-DD
                    folder_date = datetime.strptime(item, "%Y-%m-%d")
                    if folder_date < cutoff_date:
                        # Recursively delete the directory
                        for root, dirs, files in os.walk(item_path, topdown=False):
                            for name in files:
                                os.remove(os.path.join(root, name))
                            for name in dirs:
                                os.rmdir(os.path.join(root, name))
                        os.rmdir(item_path)
                        print(f"Deleted old log directory: {item_path}")
                except ValueError:
                    # Skip directories that don't match the expected date format
                    pass

    def _setup_logger(self):
        """Configures the root logger with file, console, and Qt handlers."""
        # Get the root logger
        self.logger = logging.getLogger("EnergyMeterApp")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent adding handlers multiple times if instantiated again
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Formatters
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | [%(threadName)s] | %(name)s | %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

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
