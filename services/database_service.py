import mysql.connector
from mysql.connector import errorcode
import logging
from typing import Optional, Dict, Any

class DatabaseService:
    """
    DatabaseService handles MySQL connections and operations for storing test results.
    """
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.connection = None
        
    def connect(self):
        """Establishes connection and creates database/table if not exists."""
        try:
            # First connect without database to create it if necessary
            conn = mysql.connector.connect(
                host=self.config.get('host', 'localhost'),
                user=self.config.get('user', 'root'),
                password=self.config.get('password', '')
            )
            cursor = conn.cursor()
            db_name = self.config.get('database', 'meter_test_db')
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            conn.close()

            # Now connect to the specific database
            self.connection = mysql.connector.connect(
                host=self.config.get('host', 'localhost'),
                user=self.config.get('user', 'root'),
                password=self.config.get('password', ''),
                database=db_name
            )
            self._create_table()
            self.logger.info(f"Connected to MySQL database: {db_name}")
        except mysql.connector.Error as err:
            self.logger.error(f"MySQL Connection Error: {err}")
            raise

    def _create_table(self):
        """Creates the test_results table if it doesn't exist."""
        table_schema = """
        CREATE TABLE IF NOT EXISTS test_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            meter_serial_number VARCHAR(255) NOT NULL,
            g2 VARCHAR(10),
            g3 VARCHAR(10),
            g5 VARCHAR(10),
            g6 VARCHAR(10),
            g7 VARCHAR(10),
            overall_results VARCHAR(10)
        )
        """
        cursor = self.connection.cursor()
        cursor.execute(table_schema)
        self.connection.commit()
        cursor.close()

    def find_latest_incomplete_record(self, serial_number: str, test_type: str) -> Optional[int]:
        """
        Finds the latest record for a meter where the specific test column is NULL or empty.
        Returns the row ID if found.
        """
        if not self.connection or not self.connection.is_connected():
            self.connect()

        # Only check columns that exist in the schema
        valid_columns = ['g2', 'g3', 'g5', 'g6', 'g7']
        if test_type not in valid_columns:
            return None

        query = f"""
            SELECT id FROM test_results 
            WHERE meter_serial_number = %s 
            AND ({test_type} IS NULL OR {test_type} = '')
            ORDER BY timestamp DESC LIMIT 1
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (serial_number,))
        result = cursor.fetchone()
        cursor.close()
        
        return result[0] if result else None

    def create_new_record(self, serial_number: str) -> int:
        """Creates a new record for a meter and returns its ID."""
        if not self.connection or not self.connection.is_connected():
            self.connect()

        query = "INSERT INTO test_results (meter_serial_number) VALUES (%s)"
        cursor = self.connection.cursor()
        cursor.execute(query, (serial_number,))
        self.connection.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return new_id

    def update_test_result(self, row_id: int, test_type: str, result: str):
        """Updates a specific test result in an existing row."""
        if not self.connection or not self.connection.is_connected():
            self.connect()

        valid_columns = ['g2', 'g3', 'g5', 'g6', 'g7', 'overall_results']
        if test_type not in valid_columns:
            self.logger.error(f"Invalid test column: {test_type}")
            return

        query = f"UPDATE test_results SET {test_type} = %s WHERE id = %s"
        cursor = self.connection.cursor()
        cursor.execute(query, (result, row_id))
        self.connection.commit()
        cursor.close()
        self.logger.info(f"Updated {test_type} result for row {row_id}: {result}")

    def close(self):
        """Closes the connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("MySQL connection closed.")
