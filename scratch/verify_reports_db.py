import sys
import os

# Adjust path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.config_service import ConfigService
from services.database_service import DatabaseService

def main():
    print("Initializing ConfigService...")
    config_service = ConfigService()
    config_service.load_config()
    
    db_config = config_service.get_database_config()
    print(f"Connecting to database '{db_config.get('database')}'...")
    
    db = DatabaseService(db_config)
    db.connect()
    
    cursor = db.connection.cursor()
    
    # 1. Verify failure_reason column
    print("Verifying 'failure_reason' column in 'test_results'...")
    cursor.execute("SHOW COLUMNS FROM test_results LIKE 'failure_reason'")
    col = cursor.fetchone()
    if col:
        print("-> SUCCESS: 'failure_reason' column exists.")
    else:
        print("-> FAILURE: 'failure_reason' column does not exist.")
        
    # 2. Verify test_run_details table
    print("Verifying 'test_run_details' table...")
    cursor.execute("SHOW TABLES LIKE 'test_run_details'")
    tbl = cursor.fetchone()
    if tbl:
        print("-> SUCCESS: 'test_run_details' table exists.")
    else:
        print("-> FAILURE: 'test_run_details' table does not exist.")
        
    # 3. Simulate inserting a run with multiple sub-tests (G7)
    print("Simulating test session insertion...")
    session_id = db.create_new_record("VERIFY_TEST_METER")
    print(f"-> Created session ID: {session_id}")
    
    # Insert main test G3
    print("Logging G3 main test run...")
    db.save_test_run_detail(session_id, "g3", "PASS", is_sub_test=False)
    
    # Insert G7 run 1
    print("Logging G7 run 1 (sub-test)...")
    db.save_test_run_detail(session_id, "g7", "PASS", is_sub_test=True)
    
    # Insert G7 run 2 (e.g. run again as part of G3 sequence)
    print("Logging G7 run 2 (sub-test)...")
    db.save_test_run_detail(session_id, "g7", "FAIL", "Energy delta check failed.", is_sub_test=True)
    
    # Update main results
    print("Finalizing main test outcomes...")
    db.update_test_result(session_id, "g3", "PASS")
    db.update_test_result(session_id, "g7", "FAIL")
    db.update_test_result(session_id, "overall_results", "FAIL")
    db.update_test_result(session_id, "failure_reason", "G7 sub-test failed: Energy delta check failed.")
    
    # Fetch details
    print("Fetching logged details...")
    runs = db.get_test_run_details(session_id)
    print(f"-> Found {len(runs)} execution logs for session {session_id}:")
    for run in runs:
        print(f"   * [{run['run_timestamp']}] {run['test_type'].upper()}: {run['status']} (Sub-test: {run['is_sub_test']}) - Error: {run['failure_reason']}")
        
    # Clean up test record
    print("Cleaning up simulated record...")
    cursor.execute(f"DELETE FROM test_results WHERE id = {session_id}")
    db.connection.commit()
    print("-> Cleanup complete.")
    
    cursor.close()
    db.close()
    print("Verification finished successfully!")

if __name__ == "__main__":
    main()
