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
        """Creates the necessary tables if they don't exist."""
        cursor = self.connection.cursor()
        
        # 1. Test Results Table
        table_results = """
        CREATE TABLE IF NOT EXISTS test_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            meter_serial_number VARCHAR(255) NOT NULL,
            g2 VARCHAR(10),
            g3 VARCHAR(10),
            g5 VARCHAR(10),
            g6 VARCHAR(10),
            g7 VARCHAR(10),
            overall_results VARCHAR(10),
            failure_reason TEXT
        )
        """
        cursor.execute(table_results)

        # Dynamic schema migration: add failure_reason column if it doesn't exist (for existing tables)
        try:
            cursor.execute("SHOW COLUMNS FROM test_results LIKE 'failure_reason'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE test_results ADD COLUMN failure_reason TEXT AFTER overall_results")
                self.connection.commit()
        except mysql.connector.Error as err:
            self.logger.error(f"Migration error (failure_reason): {err}")
            
        # 4. Test Run Details Table (to capture multiple G7 sub-tests and precise failure details)
        table_run_details = """
        CREATE TABLE IF NOT EXISTS test_run_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            result_id INT NOT NULL,
            test_type VARCHAR(50) NOT NULL,
            run_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) NOT NULL,
            failure_reason TEXT,
            is_sub_test BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (result_id) REFERENCES test_results(id) ON DELETE CASCADE
        )
        """
        cursor.execute(table_run_details)

        # 2. Test Suites Table
        table_suites = """
        CREATE TABLE IF NOT EXISTS test_suites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(table_suites)

        # 3. Test Steps Table
        table_steps = """
        CREATE TABLE IF NOT EXISTS test_steps (
            id INT AUTO_INCREMENT PRIMARY KEY,
            suite_id INT NOT NULL,
            step_type VARCHAR(50) NOT NULL,
            parameters_json TEXT,
            weight FLOAT DEFAULT 10.0,
            estimated_duration FLOAT DEFAULT 5.0,
            sequence_order INT DEFAULT 0,
            FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE
        )
        """
        cursor.execute(table_steps)
        
        self.connection.commit()
        cursor.close()

    # --- Test Suite Management ---

    def get_all_test_suites(self) -> list:
        """Fetches all test suites from the database."""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        query = "SELECT * FROM test_suites ORDER BY name ASC"
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)
        suites = cursor.fetchall()
        cursor.close()
        return suites

    def get_test_suite_steps(self, suite_id: int) -> list:
        """Fetches all steps for a specific test suite."""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        query = "SELECT * FROM test_steps WHERE suite_id = %s ORDER BY sequence_order ASC"
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, (suite_id,))
        steps = cursor.fetchall()
        cursor.close()
        return steps

    def save_test_suite(self, name: str, description: str, steps: list, suite_id: Optional[int] = None) -> int:
        """Saves or updates a test suite and its steps."""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        cursor = self.connection.cursor()
        try:
            if suite_id:
                # Update existing suite
                query = "UPDATE test_suites SET name = %s, description = %s WHERE id = %s"
                cursor.execute(query, (name, description, suite_id))
                # Clear existing steps to re-insert
                cursor.execute("DELETE FROM test_steps WHERE suite_id = %s", (suite_id,))
            else:
                # Create new suite
                query = "INSERT INTO test_suites (name, description) VALUES (%s, %s)"
                cursor.execute(query, (name, description))
                suite_id = cursor.lastrowid
            
            # Insert steps
            import json
            step_query = """
                INSERT INTO test_steps (suite_id, step_type, parameters_json, weight, estimated_duration, sequence_order)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            for i, step in enumerate(steps):
                params_json = json.dumps(step.get('parameters', {}))
                cursor.execute(step_query, (
                    suite_id, 
                    step.get('step_type'), 
                    params_json, 
                    step.get('weight', 10.0), 
                    step.get('estimated_duration', 5.0),
                    i
                ))
            
            self.connection.commit()
            return suite_id
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Failed to save test suite: {e}")
            raise
        finally:
            cursor.close()

    def delete_test_suite(self, suite_id: int):
        """Deletes a test suite and its steps (via cascade)."""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        cursor = self.connection.cursor()
        try:
            cursor.execute("DELETE FROM test_suites WHERE id = %s", (suite_id,))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Failed to delete test suite: {e}")
            raise
        finally:
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

        valid_columns = ['g2', 'g3', 'g5', 'g6', 'g7', 'overall_results', 'failure_reason']
        if test_type not in valid_columns:
            self.logger.error(f"Invalid test column: {test_type}")
            return

        query = f"UPDATE test_results SET {test_type} = %s WHERE id = %s"
        cursor = self.connection.cursor()
        cursor.execute(query, (result, row_id))
        self.connection.commit()
        cursor.close()
        self.logger.info(f"Updated {test_type} result for row {row_id}: {result}")

    def save_test_run_detail(self, result_id: int, test_type: str, status: str, failure_reason: Optional[str] = None, is_sub_test: bool = False):
        """Saves a detailed test run entry."""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        cursor = self.connection.cursor()
        query = """
            INSERT INTO test_run_details (result_id, test_type, status, failure_reason, is_sub_test)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (result_id, test_type, status, failure_reason, is_sub_test))
            self.connection.commit()
            self.logger.info(f"Logged run detail for {test_type} (Result ID {result_id}): {status}")
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Failed to log test run detail: {e}")
        finally:
            cursor.close()

    def get_test_run_details(self, result_id: int) -> list:
        """Fetches all detailed runs for a specific session/result ID."""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        query = "SELECT * FROM test_run_details WHERE result_id = %s ORDER BY run_timestamp ASC"
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, (result_id,))
        details = cursor.fetchall()
        cursor.close()
        return details

    def get_all_test_results(self, filters: Optional[Dict[str, Any]] = None) -> list:
        """Fetches test results with optional filtering."""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        query = "SELECT * FROM test_results WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('serial_number'):
                query += " AND meter_serial_number LIKE %s"
                params.append(f"%{filters['serial_number']}%")
            if filters.get('status') and filters['status'] != 'All':
                query += " AND overall_results = %s"
                params.append(filters['status'])
            if filters.get('start_date'):
                query += " AND timestamp >= %s"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                query += " AND timestamp <= %s"
                params.append(filters['end_date'])
                
        query += " ORDER BY timestamp DESC"
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        cursor.close()
        return results

    def close(self):
        """Closes the connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("MySQL connection closed.")
