import json
import os
import uuid
import logging

class ProfileManager:
    """
    Manages Meter Profiles stored in configs/meter_profiles.json.
    """
    def __init__(self, config_path=None):
        self.logger = logging.getLogger("ProfileManager")
        if not config_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.config_path = os.path.join(base_dir, "configs", "meter_profiles.json")
        else:
            self.config_path = config_path
            
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            default_data = {
                "profiles": []
            }
            with open(self.config_path, 'w') as f:
                json.dump(default_data, f, indent=2)

    def _load_data(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load meter profiles: {e}")
            return {"profiles": []}

    def _save_data(self, data):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save meter profiles: {e}")
            return False

    def get_all_profiles(self):
        """Returns a list of all profiles."""
        data = self._load_data()
        return data.get("profiles", [])

    def get_profile(self, profile_id):
        """Returns a specific profile by ID."""
        profiles = self.get_all_profiles()
        for p in profiles:
            if p.get("id") == profile_id:
                return p
        return None

    def save_profile(self, profile_data):
        """Creates or updates a profile."""
        data = self._load_data()
        profiles = data.get("profiles", [])
        
        if "id" not in profile_data or not profile_data["id"]:
            profile_data["id"] = str(uuid.uuid4())
            profiles.append(profile_data)
        else:
            # Update existing
            for i, p in enumerate(profiles):
                if p.get("id") == profile_data["id"]:
                    profiles[i] = profile_data
                    break
            else:
                # ID provided but not found, append it
                profiles.append(profile_data)
                
        data["profiles"] = profiles
        return self._save_data(data)

    def delete_profile(self, profile_id):
        """Deletes a profile by ID."""
        data = self._load_data()
        profiles = data.get("profiles", [])
        initial_length = len(profiles)
        
        data["profiles"] = [p for p in profiles if p.get("id") != profile_id]
        
        if len(data["profiles"]) < initial_length:
            return self._save_data(data)
        return False
