import streamlit as st
import json
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RUNDATA_DIR = DATA_DIR / "rundata"  # [NEW] 샘플 데이터 폴더
MASTER_DB_FILE = DATA_DIR / "master_ship.json"

@st.cache_data
def load_master_ship_db():
    if MASTER_DB_FILE.exists():
        try:
            with open(MASTER_DB_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                if isinstance(data, dict): return data, f"✅ Loaded ({len(data)} ships)"
                elif isinstance(data, list):
                    converted_db = {}
                    for item in data: converted_db.update(item)
                    return converted_db, f"✅ Loaded (Merged {len(converted_db)} entries)"
                return {}, "❌ Unknown Format"
        except json.JSONDecodeError as e: return {}, f"❌ JSON Error: {e}"
        except Exception as e: return {}, f"❌ Error: {e}"
    return {}, "⚠️ No File"

# [NEW] 샘플 데이터 목록 가져오기
def get_sample_files():
    if not RUNDATA_DIR.exists(): return []
    return [f.name for f in RUNDATA_DIR.glob("*.json")]

# [NEW] 샘플 데이터 읽기
def load_sample_file(filename):
    file_path = RUNDATA_DIR / filename
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except: return None
    return None

class FleetManager:
    def __init__(self): pass
    
    def get_all_options(self): 
        return st.session_state.my_fleet
    
    def update_fleet_from_upload(self, new_fleet_list):
        if isinstance(new_fleet_list, list) and len(new_fleet_list) > 0:
            st.session_state.my_fleet = new_fleet_list
            return True
        return False
        
    def add_ship_from_master(self, model_name, master_db):
        if len(st.session_state.my_fleet) >= 50: return False, "Fleet is full."
        if model_name in master_db:
            spec = master_db[model_name]
            for s in st.session_state.my_fleet:
                if s['model'] == spec.get('name', model_name): return False, "Already owned."
            new_ship = {
                "id": str(uuid.uuid4())[:8],
                "man": spec.get("manufacturer", "Unknown"),
                "model": spec.get("name", model_name),
                "capa": spec.get("cargo", 0),
                "max_box": spec.get("cargo", 0),
                "role": spec.get("role", "N/A"),
                "size": spec.get("size", "N/A"),
                "pledge": spec.get("pledge", "-"),
                "auec": spec.get("auec", "-"),
                "url": spec.get("url", "#")
            }
            st.session_state.my_fleet.append(new_ship)
            return True, f"{model_name} Added!"
        return False, "Not in Master DB."
        
    def delete_ship(self, ship_id):
        if len(st.session_state.my_fleet) <= 1: return False, "Cannot delete last ship."
        st.session_state.my_fleet = [s for s in st.session_state.my_fleet if s['id'] != ship_id]
        return True, "Removed."
        
    def get_ship_by_id(self, ship_id):
        return next((s for s in st.session_state.my_fleet if s["id"] == ship_id), None)