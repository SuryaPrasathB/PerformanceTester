import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.database_service import DatabaseService

def test_db_logic():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("DB_TEST")
    
    # Mock config (using root since I don't want to mess with user's DB yet if it doesn't exist)
    # But wait, I'll use the actual config if possible but with a test DB name
    config = {
        "host": "localhost",
        "user": "root",
        "password": "your_password", # User needs to fill this
        "database": "test_meter_db_delete_me"
    }
    
    db = DatabaseService(config, logger)
    try:
        db.connect()
        print("Connected!")
        
        serial = "METER-001"
        
        # 1. Create new
        row_id = db.create_new_record(serial)
        print(f"Created row: {row_id}")
        
        # 2. Update G2
        db.update_test_result(row_id, "g2", "PASS")
        print("Updated G2 to PASS")
        
        # 3. Find incomplete for G3
        incomplete_id = db.find_latest_incomplete_record(serial, "g3")
        print(f"Incomplete G3 row found: {incomplete_id}")
        assert incomplete_id == row_id
        
        # 4. Update G3
        db.update_test_result(row_id, "g3", "FAIL")
        print("Updated G3 to FAIL")
        
        # 5. Check if G3 is still incomplete
        still_incomplete = db.find_latest_incomplete_record(serial, "g3")
        print(f"Still incomplete G3: {still_incomplete}")
        assert still_incomplete is None or still_incomplete != row_id
        
        print("\nSUCCESS: All DB logic checks out.")
        
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db_logic()
