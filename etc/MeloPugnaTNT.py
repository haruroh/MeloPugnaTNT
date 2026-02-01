import streamlit as st
import pandas as pd
import json
import os
import copy
import math
import itertools
import uuid
import time
from pathlib import Path
from datetime import datetime

# --- Page Config ---
st.set_page_config(
    page_title="MeloPugna Trade & Transport v0.27.10", 
    layout="wide", 
    initial_sidebar_state="auto"
)

# ==========================================
# [System] Constants & Path
# ==========================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
# USER_FLEET_FILE 제거 (개별 사용자 파일 저장 안 함)
MASTER_DB_FILE = DATA_DIR / "master_ship.json"

if not DATA_DIR.exists():
    DATA_DIR.mkdir()

# [System] Code Generators
def generate_loc_code(n):
    if n < 26: return chr(65 + n)
    else:
        q, r = divmod(n, 26)
        return chr(64 + q) + chr(65 + r)

K_CORE = ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하"]
def generate_item_code(n):
    l = len(K_CORE)
    if n < l: return K_CORE[n]
    else:
        q, r = divmod(n, l)
        return K_CORE[q-1] + K_CORE[r]

# [System] Smart Loader (Handles both List and Dict formats)
@st.cache_data
def load_master_ship_db():
    if MASTER_DB_FILE.exists():
        try:
            with open(MASTER_DB_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                # Case 1: Dict { "ShipA": {...} }
                if isinstance(data, dict): return data, f"✅ Loaded ({len(data)} ships)"
                # Case 2: List [ {"ShipA": {...}}, ... ]
                elif isinstance(data, list):
                    converted_db = {}
                    for item in data:
                        converted_db.update(item)
                    return converted_db, f"✅ Loaded (Merged {len(converted_db)} entries)"
                return {}, "❌ Unknown Format"
        except json.JSONDecodeError as e: return {}, f"❌ JSON Error: {e}"
        except Exception as e: return {}, f"❌ Error: {e}"
    return {}, "⚠️ No File"

MASTER_SHIP_DB, DB_STATUS = load_master_ship_db()

# Extract Manufacturers
if MASTER_SHIP_DB:
    try:
        MANUFACTURERS = sorted(list(set([v.get("manufacturer", "Unknown") for v in MASTER_SHIP_DB.values()])))
    except:
        MANUFACTURERS = ["Anvil", "Aegis", "Argo", "Crusader", "Drake", "MISC", "RSI", "CNOU", "Gatac"]
else:
    MANUFACTURERS = ["Anvil", "Aegis", "Argo", "Crusader", "Drake", "MISC", "RSI", "CNOU", "Gatac"]

VALID_CONTAINER_SIZES = [1, 2, 4, 8, 16, 24, 32]

# [Data] Defaults
PRESET_LOC_NAMES = ["Seraphim Station", "Orison", "Grim HEX", "Area18", "Baijini Point", "New Babbage", "Port Tressler", "Lorville", "Everus Harbor", "Pyrollis"]
PRESET_ITEM_NAMES = ["Medical Supplies", "Distilled Spirits", "Stims", "Processed Food", "Scrap", "RMC", "Gold", "Laranite", "Agricium", "Waste"]
# 장소와 아이템 기본값 개수
DEFAULT_LENGTH = 10
# 장소 및 아이템 기본 매핑
DEFAULT_LOC_MAP = {generate_loc_code(i): (PRESET_LOC_NAMES[i] if i < len(PRESET_LOC_NAMES) else "") for i in range(DEFAULT_LENGTH)}
DEFAULT_ITEM_MAP = {generate_item_code(i): (PRESET_ITEM_NAMES[i] if i < len(PRESET_ITEM_NAMES) else "") for i in range(DEFAULT_LENGTH)}

DEFAULT_MISSIONS = [
    {"name": "💊 Seraphim Medical Run", "reward": 45000, "tasks": [{"Origin": "B", "Dest": "A", "Item": "가", "Qty": 10}, {"Origin": "A", "Dest": "C", "Item": "나", "Qty": 5}]} 
    , {"name": "💊 Seraphim Stims Run", "reward": 54000, "tasks": [{"Origin": "A", "Dest": "C", "Item": "다", "Qty": 10}, {"Origin": "A", "Dest": "B", "Item": "다", "Qty": 5}, {"Origin": "A", "Dest": "D", "Item": "다", "Qty": 5}]}
]

INITIAL_FLEET = [
    {"id": "s_001", "man": "Drake ", "model": "Cutlass Black", "capa": 46, "max_box": 16, "role": "Light Freight / Medium Fighter", "size": "Medium", "pledge": "$110.00", "auec": "2,117,400 aUEC", "url": "https://www.spviewer.eu/performance?ship=drak_cutlass_black"},
    {"id": "s_002", "man": "Crusader", "model": "Mercury Star Runner", "capa": 114, "max_box": 24, "role": "Medium Freight", "size": "Large", "pledge": "$260.00", "auec": "12,285,000 aUEC", "url": "https://www.spviewer.eu/performance?ship=crus_star_runner"},
    {"id": "s_003", "man": "Argo", "model": "Raft", "capa": 192, "max_box": 32, "role": "Medium Freight", "size": "Large", "pledge": "$125.00", "auec": "3,543,750 aUEC", "url": "https://www.spviewer.eu/performance?ship=argo_raft"}
]

RICH_DEFAULTS = {
    "language": "KR", "current_ship_id": "s_002",
    "loc_map": copy.deepcopy(DEFAULT_LOC_MAP), "item_map": copy.deepcopy(DEFAULT_ITEM_MAP),
    "mission_groups": copy.deepcopy(DEFAULT_MISSIONS), "presets": [],
    "my_fleet": copy.deepcopy(INITIAL_FLEET) # Isolated Fleet
}

# ==========================================
# [Core Logic] Helper Functions
# ==========================================
def safe_int(val):
    try: return int(float(val)) if val is not None and not (isinstance(val, float) and (math.isnan(val) or math.isinf(val))) else 0
    except: return 0

def format_option(code, map_dict):
    name = map_dict.get(code, "")
    return f"{name} ({code})" if name else code

def parse_option(formatted_str):
    if "(" in formatted_str and formatted_str.endswith(")"): return formatted_str.split("(")[-1].strip(")")
    return formatted_str

def get_loc_label(code): return st.session_state.loc_map.get(code, code)
def get_item_label(code): return st.session_state.item_map.get(code, code)

# ==========================================
# [Core Logic] Fleet Manager
# ==========================================
class FleetManager:
    def __init__(self):
        pass

    def get_all_options(self):
        return st.session_state.my_fleet

    def update_fleet_from_upload(self, new_fleet_list):
        if isinstance(new_fleet_list, list) and len(new_fleet_list) > 0:
            st.session_state.my_fleet = new_fleet_list
            return True
        return False

    def add_ship_from_master(self, model_name):
        if len(st.session_state.my_fleet) >= 50: return False, "Fleet is full."
        
        if model_name in MASTER_SHIP_DB:
            spec = MASTER_SHIP_DB[model_name]
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

# ==========================================
# [Core Logic] Algorithms
# ==========================================
def flatten_groups(groups):
    flat = []
    for g in groups:
        for t in g.get('tasks', []):
            t_safe = t.copy(); t_safe['Qty'] = safe_int(t.get('Qty', 0)); flat.append(t_safe)
    return flat

def find_smart_paths(tasks, start, firsts, lasts, round_trip):
    locs = set()
    for t in tasks: locs.add(t['Origin']); locs.add(t['Dest'])
    fixed = {start} | set(firsts) | set(lasts)
    middle = list(locs - fixed)
    valid = []
    def check_complete(path):
        pending = [t.copy() for t in tasks]; onboard = []
        for stop in path:
            onboard = [i for i in onboard if i['Dest'] != stop]
            new_pending = []
            for i in pending:
                if i['Origin'] == stop: onboard.append(i)
                else: new_pending.append(i)
            pending = new_pending
        return not pending and not onboard
    for perm in itertools.permutations(middle):
        raw = [start] + list(firsts) + list(perm) + list(lasts)
        if round_trip: raw.append(start)
        clean = []
        for l in raw:
            if not clean or clean[-1] != l: clean.append(l)
        if check_complete(clean):
            if clean not in valid: valid.append(clean)
    return sorted(valid, key=len)

# ==========================================
# [UI] Initialize Session
# ==========================================
if 'loc_map' not in st.session_state: st.session_state.loc_map = copy.deepcopy(RICH_DEFAULTS["loc_map"])
if 'item_map' not in st.session_state: st.session_state.item_map = copy.deepcopy(RICH_DEFAULTS["item_map"])
if 'mission_groups' not in st.session_state: st.session_state.mission_groups = copy.deepcopy(RICH_DEFAULTS["mission_groups"])
if 'presets' not in st.session_state: st.session_state.presets = copy.deepcopy(RICH_DEFAULTS["presets"])
if 'current_lang' not in st.session_state: st.session_state.current_lang = RICH_DEFAULTS["language"]
if 'current_ship_id' not in st.session_state: st.session_state.current_ship_id = RICH_DEFAULTS["current_ship_id"]
if 'my_fleet' not in st.session_state: st.session_state.my_fleet = copy.deepcopy(RICH_DEFAULTS["my_fleet"])

if 'staging_tasks' not in st.session_state: st.session_state.staging_tasks = []
if 'calc_value' not in st.session_state: st.session_state.calc_value = "0"
if 'contract_name_input' not in st.session_state: st.session_state.contract_name_input = ""
if 'found_routes' not in st.session_state: st.session_state.found_routes = []
if 'route_str' not in st.session_state: st.session_state.route_str = ""
if 'processed_file_id' not in st.session_state: st.session_state.processed_file_id = ""

fleet_mgr = FleetManager()

LOC_CODES = list(st.session_state.loc_map.keys())
ITEM_CODES = list(st.session_state.item_map.keys())

# --- Translation ---
TRANS = {
    "KR": {
        "app_title": "MeloPugna Trade & Transport", "app_subtitle": "스타시티즌 무역 및 화물 운송 최적화 솔루션",
        "sidebar_title": "⚙️ 설정 및 함선", "upload_label": "📂 설정 불러오기", "download_label": "💾 설정 저장하기",
        "lang_select": "언어", "ship_select": "운용 함선 선택", "map_expander": "🗺️ 이름 및 상품 매핑", 
        "ship_add_expander": "🚀 함선 추가 (마스터 DB 검색)", "ship_search_label": "함선 모델명 검색", 
        "ship_add_btn": "내 함선 목록에 추가", "ship_del_btn": "현재 함선 삭제",
        "hud_label": "현재 운용 함선",
        "hud_stat_capa": "최대 적재량", "hud_stat_role": "역할", "hud_stat_size": "크기",
        "hud_stat_pledge": "서약 금액", "hud_stat_auec": "인게임 가격",
        "hud_metric_cargo": "운송 화물 수", "hud_metric_contract": "계약 현황", "hud_metric_rev": "예상 수익",
        "unit_scu": "SCU", "unit_groups": "건", "overload": "⚠️ 용량 초과", "success": "완료",
        "unload": "하차", "load": "상차",
        "tab_1": "➕ 계약 생성", "tab_2": "📋 계약 관리", "tab_3": "🚚 시뮬레이션",
        "stg_header": "1️⃣ 세부 목표 입력", "stg_add": "추가", "stg_list": "📝 목표 리스트", "stg_empty": "목표 없음",
        "calc_header": "2️⃣ 계약 확정", "calc_commit": "등록 완료", "calc_reset": "초기화",
        "name_label": "계약 이름", "name_placeholder": "예: 약품런", "warn_no_task": "목표가 없습니다.", "success_commit": "등록됨!",
        "grp_manage": "계약 목록", "grp_del": "삭제", "edit_name": "이름 수정", "edit_reward": "보상금 수정",
        "save_btn": "💾 프리셋으로 저장", "clear_btn": "초기화", "calc_btn": "🔍 경로 탐색", "sim_header": "탐색 결과",
        "select_route": "경로 선택", "return_start": "왕복", "start_loc": "시작 위치",
        "adv_opt": "고급 설정", "opt_first": "첫 경유지", "opt_last": "마지막 경유지",
        "preset_sec": "📂 프리셋 관리", "load_btn": "불러오기", "del_preset": "삭제", "tab1_preset": "📂 프리셋에서 불러오기",
        "col_origin": "출발지", "col_dest": "도착지", "col_item": "화물명", "col_qty": "수량",
        "master_db_missing": "⚠️ 마스터 DB 파일이 없습니다.", "ship_info": "ℹ️ {} ({} SCU)",
        "save_filename_label": "저장할 파일명", "save_path_info": "ℹ️ 브라우저 기본 다운로드 폴더에 저장됩니다.",
        "link_spviewer": "🔗 SPViewer 상세 정보", "add_loc_btn": "➕ 코드 추가", "add_item_btn": "➕ 코드 추가",
        "clear_loc_btn": "🗑️ 이름 지우기", "reset_loc_btn": "🔄 기본값 복원 (A~Z)", 
        "clear_item_btn": "🗑️ 이름 지우기", "reset_item_btn": "🔄 기본값 복원 (가~하)",
        "limit_reached": "최대 개수(50개)에 도달했습니다.",
        "footer_plan": "기획", "footer_code": "코드 & 로직", "footer_ai_notice": "본 소프트웨어는 AI 기술과의 협업으로 제작되었습니다."
    },
    "EN": {
        "app_title": "MeloPugna Trade & Transport", "app_subtitle": "Star Citizen Trade & Cargo Hauling Optimization Solution",
        "footer_plan": "Planning", "footer_code": "Code & Logic", "footer_ai_notice": "This software was developed in collaboration with AI technology.",
        "sidebar_title": "Settings", "upload_label": "📂 Load", "download_label": "💾 Save",
        "lang_select": "Language", "ship_select": "Select Ship", "map_expander": "Map Names", 
        "ship_add_expander": "🚀 Add Ship", "ship_search_label": "Search Model", 
        "ship_add_btn": "Add to Fleet", "ship_del_btn": "Delete Ship",
        "hud_label": "PILOTING",
        "hud_stat_capa": "Capacity", "hud_stat_role": "Role", "hud_stat_size": "Size",
        "hud_stat_pledge": "Pledge", "hud_stat_auec": "aUEC",
        "hud_metric_cargo": "Total Cargo", "hud_metric_contract": "Active Contracts", "hud_metric_rev": "Est. Revenue",
        "unit_scu": "SCU", "unit_groups": "Groups", "overload": "OVERLOAD", "success": "Done",
        "unload": "Unload", "load": "Load",
        "tab_1": "➕ Add", "tab_2": "📋 Manage", "tab_3": "🚚 Simulate",
        "stg_header": "1️⃣ Sub-tasks", "stg_add": "Add", "stg_list": "📝 List", "stg_empty": "Empty",
        "calc_header": "2️⃣ Finalize", "calc_commit": "Commit", "calc_reset": "Clear",
        "name_label": "Name", "name_placeholder": "e.g. Run", "warn_no_task": "No tasks", "success_commit": "Added!",
        "grp_manage": "Contracts", "grp_del": "Del", "edit_name": "Edit Name", "edit_reward": "Edit Reward",
        "save_btn": "💾 Save as Preset", "clear_btn": "Reset", "calc_btn": "🔍 Search", "sim_header": "Results",
        "select_route": "Select", "return_start": "Round Trip", "start_loc": "Start",
        "adv_opt": "Advanced", "opt_first": "First Stop", "opt_last": "Last Stop",
        "preset_sec": "📂 Presets", "load_btn": "Load", "del_preset": "Del", "tab1_preset": "📂 Load from Preset",
        "conflict_msg": "Conflict", "conflict_desc": "Name exists.",
        "col_origin": "Origin", "col_dest": "Destination", "col_item": "Commodity", "col_qty": "Quantity",
        "master_db_missing": "⚠️ Master DB missing.", "ship_info": "ℹ️ {} ({} SCU)",
        "save_filename_label": "File Name", "save_path_info": "ℹ️ Saved to browser default folder.",
        "link_spviewer": "🔗 SPViewer Details", "add_loc_btn": "➕ Add Code", "add_item_btn": "➕ Add Code",
        "clear_loc_btn": "🗑️ Clear Names", "reset_loc_btn": "🔄 Factory Reset", 
        "clear_item_btn": "🗑️ Clear Names", "reset_item_btn": "🔄 Factory Reset",
        "limit_reached": "Limit reached."
    }
}
L_CODE = st.session_state.current_lang
T = TRANS[L_CODE]

# --- CALLBACKS ---
def add_staging_task_callback(origin, dest, item, qty):
    st.session_state.staging_tasks.append({"Origin": origin, "Dest": dest, "Item": item, "Qty": int(qty)})

def clear_staging_callback(): st.session_state.staging_tasks = []

def load_preset_to_staging_callback(preset_idx):
    if st.session_state.presets:
        loaded = copy.deepcopy(st.session_state.presets[preset_idx])
        st.session_state.staging_tasks = loaded['tasks']
        st.session_state.calc_value = str(loaded.get('reward', 0))
        st.session_state.contract_name_input = loaded.get('name', "")

def commit_contract_callback():
    if not st.session_state.staging_tasks: return 
    c_name = st.session_state.contract_name_input
    fn = c_name if c_name.strip() else f"Contract #{len(st.session_state.mission_groups)+1}"
    grp = {"name": fn, "reward": int(st.session_state.calc_value), "tasks": copy.deepcopy(st.session_state.staging_tasks)}
    st.session_state.mission_groups.append(grp)
    st.session_state.staging_tasks = []; st.session_state.calc_value = "0"; st.session_state.contract_name_input = ""

def load_preset_to_manage_callback(preset_idx):
    if st.session_state.presets:
        tgt = st.session_state.presets[preset_idx]
        st.session_state.mission_groups.append(copy.deepcopy(tgt))

def delete_preset_callback(preset_idx): st.session_state.presets.pop(preset_idx)
def delete_group_callback(grp_idx): st.session_state.mission_groups.pop(grp_idx)

def save_preset_callback_tab1():
    if not st.session_state.staging_tasks: return
    c_name = st.session_state.contract_name_input
    fn = c_name if c_name.strip() else f"Contract #{len(st.session_state.mission_groups)+1}"
    new_p = {"name": fn, "reward": int(st.session_state.calc_value), "tasks": copy.deepcopy(st.session_state.staging_tasks)}
    existing_names = [p['name'] for p in st.session_state.presets]
    base_name = new_p['name']; count = 1
    while new_p['name'] in existing_names: new_p['name'] = f"{base_name} ({count})"; count += 1
    st.session_state.presets.append(new_p)

def save_preset_callback_tab2(grp_idx):
    grp = st.session_state.mission_groups[grp_idx]; new_p = copy.deepcopy(grp)
    existing_names = [p['name'] for p in st.session_state.presets]
    base_name = new_p['name']; count = 1
    while new_p['name'] in existing_names: new_p['name'] = f"{base_name} ({count})"; count += 1
    st.session_state.presets.append(new_p)

def clear_all_callback(): st.session_state.mission_groups = []
def update_group_name_callback(idx, key): st.session_state.mission_groups[idx]['name'] = st.session_state[key]
def update_group_reward_callback(idx, key): st.session_state.mission_groups[idx]['reward'] = int(st.session_state[key])

def add_loc_code_callback():
    curr_len = len(st.session_state.loc_map)
    if curr_len < 50: st.session_state.loc_map[generate_loc_code(curr_len)] = ""
    else: st.toast(T["limit_reached"])

def add_item_code_callback():
    curr_len = len(st.session_state.item_map)
    if curr_len < 50: st.session_state.item_map[generate_item_code(curr_len)] = ""
    else: st.toast(T["limit_reached"])

def clear_loc_names_callback():
    for k in st.session_state.loc_map:
        st.session_state.loc_map[k] = ""; st.session_state[f"l_{k}"] = ""

def clear_item_names_callback():
    for k in st.session_state.item_map:
        st.session_state.item_map[k] = ""; st.session_state[f"i_{k}"] = ""

def reset_loc_factory_callback():
    for k in list(st.session_state.loc_map.keys()):
        if f"l_{k}" in st.session_state: del st.session_state[f"l_{k}"]
    st.session_state.loc_map = copy.deepcopy(DEFAULT_LOC_MAP)
    for k, v in st.session_state.loc_map.items(): st.session_state[f"l_{k}"] = v

def reset_item_factory_callback():
    for k in list(st.session_state.item_map.keys()):
        if f"i_{k}" in st.session_state: del st.session_state[f"i_{k}"]
    st.session_state.item_map = copy.deepcopy(DEFAULT_ITEM_MAP)
    for k, v in st.session_state.item_map.items(): st.session_state[f"i_{k}"] = v

# --- HEADER ---
st.title(f"🚀 {T['app_title']} v0.27.10")
st.caption(T['app_subtitle'])

# --- Sidebar ---
with st.sidebar:
    st.title(T["sidebar_title"])
    if DB_STATUS.startswith("❌"): st.error(f"DB: {DB_STATUS}")
    else: st.caption(f"DB: {DB_STATUS}")
    
    uploaded = st.file_uploader(T["upload_label"], type=["json"])
    if uploaded:
        file_id = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.processed_file_id != file_id:
            try:
                d = json.load(uploaded)
                
                # [FIXED] 데이터 로드 시 위젯 Key 동기화 (화면 갱신용)
                if "loc_map" in d: 
                    st.session_state.loc_map = d["loc_map"]
                    # 위젯에도 강제 주입
                    for k, v in d["loc_map"].items():
                        st.session_state[f"l_{k}"] = v

                if "item_map" in d: 
                    st.session_state.item_map = d["item_map"]
                    # 위젯에도 강제 주입
                    for k, v in d["item_map"].items():
                        st.session_state[f"i_{k}"] = v

                if "mission_groups" in d: st.session_state.mission_groups = d["mission_groups"]
                if "presets" in d: st.session_state.presets = d["presets"]
                if "my_fleet" in d: fleet_mgr.update_fleet_from_upload(d["my_fleet"])
                
                if "current_ship_id" in d:
                    if fleet_mgr.get_ship_by_id(d["current_ship_id"]):
                        st.session_state.current_ship_id = d["current_ship_id"]
                    else:
                        all_s = fleet_mgr.get_all_options()
                        if all_s: st.session_state.current_ship_id = all_s[0]["id"]
                
                # [FIX v0.27.10] Clear Widget State to reflect loaded names/rewards
                for k in list(st.session_state.keys()):
                    if k.startswith("gn_") or k.startswith("gr_"):
                        del st.session_state[k]

                st.session_state.processed_file_id = file_id
                st.toast("Loaded Successfully! Refreshing UI...", icon="✅")
                st.rerun() 
            except Exception as e: st.error(f"Load Failed: {e}")

    st.divider()
    save_name = st.text_input(T["save_filename_label"], value=f"haru_config_{datetime.now().strftime('%Y%m%d')}.json")
    st.caption(T["save_path_info"])
    
    ex_data = {
        "current_ship_id": st.session_state.current_ship_id,
        "loc_map": st.session_state.loc_map, "item_map": st.session_state.item_map,
        "mission_groups": st.session_state.mission_groups, "presets": st.session_state.presets,
        "my_fleet": fleet_mgr.get_all_options() 
    }
    
    st.download_button(label=T["download_label"], data=json.dumps(ex_data, indent=4, ensure_ascii=False), file_name=save_name, mime="application/json", use_container_width=True)
    
    st.divider()
    lang_opt = st.selectbox(T["lang_select"], ["KR", "EN"], index=["KR", "EN"].index(st.session_state.current_lang))
    
    my_ships = fleet_mgr.get_all_options()
    s_opts = {s["id"]: f"{s['model']} [{s['man']}] ({s['capa']} SCU)" for s in my_ships}
    
    def update_ship(): pass 

    if st.session_state.current_ship_id not in s_opts:
        if my_ships: st.session_state.current_ship_id = my_ships[0]["id"]
    
    # [FIX v0.27.10] Removed index=... to prevent conflict with key=...
    st.selectbox(T["ship_select"], options=list(s_opts.keys()), format_func=lambda x: s_opts[x], key="current_ship_id", on_change=update_ship)
    
    if st.session_state.current_lang != lang_opt:
        st.session_state.current_lang = lang_opt; st.rerun()

    with st.expander(T["ship_add_expander"]):
        if not MASTER_SHIP_DB: st.warning(T["master_db_missing"])
        else:
            search_term = st.text_input(T["ship_search_label"])
            # [Optimized] Search Keys directly
            if search_term: filtered_master = [m for m in MASTER_SHIP_DB.keys() if search_term.lower() in m.lower()]
            else: filtered_master = sorted(list(MASTER_SHIP_DB.keys()))
            
            target_model = st.selectbox("Model", filtered_master)
            if target_model:
                spec = MASTER_SHIP_DB[target_model]
                st.caption(T["ship_info"].format(spec.get('name', target_model), spec.get('cargo', 0)))
                def add_ship_cb():
                    success, msg = fleet_mgr.add_ship_from_master(target_model)
                    if success: st.toast(msg, icon="🚀")
                    else: st.error(msg)
                st.button(T["ship_add_btn"], use_container_width=True, on_click=add_ship_cb)
                
    if len(my_ships) > 1:
        def del_ship_cb():
            res, msg = fleet_mgr.delete_ship(st.session_state.current_ship_id)
            if res:
                all_s = fleet_mgr.get_all_options(); st.session_state.current_ship_id = all_s[0]["id"]; st.toast(msg)
            else: st.error(msg)
        st.button(T["ship_del_btn"], type="secondary", use_container_width=True, on_click=del_ship_cb)

    st.divider()
    with st.expander(T["map_expander"]):
        t1, t2 = st.tabs(["Loc", "Item"])
        with t1:
            for c in LOC_CODES: st.session_state.loc_map[c] = st.text_input(c, st.session_state.loc_map[c], key=f"l_{c}")
            c1, c2, c3 = st.columns(3)
            c1.button(T["add_loc_btn"], on_click=add_loc_code_callback, use_container_width=True, key="btn_add_loc")
            c2.button(T["clear_loc_btn"], on_click=clear_loc_names_callback, use_container_width=True, key="btn_clear_loc")
            c3.button(T["reset_loc_btn"], on_click=reset_loc_factory_callback, use_container_width=True, key="btn_reset_loc")
        with t2:
            for c in ITEM_CODES: st.session_state.item_map[c] = st.text_input(c, st.session_state.item_map[c], key=f"i_{c}")
            c1, c2, c3 = st.columns(3)
            c1.button(T["add_item_btn"], on_click=add_item_code_callback, use_container_width=True, key="btn_add_item")
            c2.button(T["clear_item_btn"], on_click=clear_item_names_callback, use_container_width=True, key="btn_clear_item")
            c3.button(T["reset_item_btn"], on_click=reset_item_factory_callback, use_container_width=True, key="btn_reset_item")

# --- HUD ---
s_dat = fleet_mgr.get_ship_by_id(st.session_state.current_ship_id)
if not s_dat: s_dat = INITIAL_FLEET[0]

ship_name = s_dat.get('model', 'Unknown')
man_name = s_dat.get('man', 'Unknown')
url = s_dat.get('url', '#')
capa_val = s_dat.get('capa', 0)
role_val = s_dat.get('role', '-')
size_val = s_dat.get('size', '-')
pledge_val = s_dat.get('pledge', '-')
auec_val = s_dat.get('auec', '-')

flat_list = flatten_groups(st.session_state.mission_groups)
total_cargo_load = sum(task.get('Qty', 0) for task in flat_list)
cnt = len(st.session_state.mission_groups)
rew = sum(g.get('reward',0) for g in st.session_state.mission_groups)

capa_str = f"{capa_val} {T['unit_scu']}"
total_cargo_str = f"{total_cargo_load} {T['unit_scu']}"
rew_str = f"{rew:,} aUEC"
link_html = f'<div class="hud-link"><a href="{url}" target="_blank">{T["link_spviewer"]}</a></div>'

st.markdown("""
<style>
.hud-container { background: linear-gradient(135deg, #1A1A24, #0D0D12); border-radius: 12px; padding: 25px 30px; border: 1px solid #333; border-left: 6px solid #00D4FF; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
.hud-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 5px; }
.hud-ship-name { color: #FFFFFF; font-size: 2.8rem; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
.hud-manufacturer { color: #AAAAAA; font-size: 1.2rem; font-weight: 500; font-style: italic; }
.hud-link a { color: #00D4FF; font-size: 0.85rem; text-decoration: none; opacity: 0.8; transition: opacity 0.3s; margin-left: 2px; }
.hud-link a:hover { opacity: 1; text-decoration: underline; color: #FFD700; }
.hud-info-row { display: flex; gap: 20px; margin-top: 15px; flex-wrap: wrap; }
.info-item { background: rgba(255, 255, 255, 0.05); padding: 8px 12px; border-radius: 6px; border: 1px solid #444; }
.info-label { font-size: 0.8rem; color: #888; display: block; margin-bottom: 2px; }
.info-value { font-size: 1.1rem; font-weight: 700; color: #00D4FF; }
.info-value.orange { color: #FFA500; }
.hud-stats-row { display: flex; align-items: center; gap: 40px; border-top: 1px solid #333; padding-top: 15px; margin-top: 20px; }
.stat-box { display: flex; flex-direction: column; }
.stat-label { font-size: 0.8rem; color: #aaa; letter-spacing: 1px; }
.stat-value { font-size: 1.5rem; color: #EEE; font-weight: 700; }
.stat-value.gold { color: #FFD700; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hud-container">
    <div class="hud-header">
        <span class="hud-ship-name">{ship_name}</span>
        <span class="hud-manufacturer">{man_name}</span>
    </div>
    {link_html}
    <div class="hud-info-row">
        <div class="info-item"><span class="info-label">{T['hud_stat_capa']}</span><span class="info-value">{capa_str}</span></div>
        <div class="info-item"><span class="info-label">{T['hud_stat_role']}</span><span class="info-value orange">{role_val}</span></div>
        <div class="info-item"><span class="info-label">{T['hud_stat_size']}</span><span class="info-value">{size_val}</span></div>
        <div class="info-item"><span class="info-label">{T['hud_stat_pledge']}</span><span class="info-value">{pledge_val}</span></div>
        <div class="info-item"><span class="info-label">{T['hud_stat_auec']}</span><span class="info-value">{auec_val}</span></div>
    </div>
    <div class="hud-stats-row">
        <div class="stat-box"><span class="stat-label">{T['hud_metric_cargo']}</span><span class="stat-value">{total_cargo_str}</span></div>
        <div class="stat-box"><span class="stat-label">{T['hud_metric_contract']}</span><span class="stat-value">{cnt} {T['unit_groups']}</span></div>
        <div class="stat-box"><span class="stat-label">{T['hud_metric_rev']}</span><span class="stat-value gold">{rew_str}</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([T["tab_1"], T["tab_2"], T["tab_3"]])

# Tab 1: Add (Standard UI)
with tab1:
    with st.expander(T["tab1_preset"], expanded=False):
        if st.session_state.presets:
            p_opts = [f"{p.get('name','?')} ({len(p.get('tasks',[]))} tasks)" for p in st.session_state.presets]
            sel_p_idx = st.selectbox("Select Preset to Load", range(len(p_opts)), format_func=lambda x: p_opts[x], key="t1_preset_sel")
            st.button(T["load_btn"], key="t1_load_btn", on_click=load_preset_to_staging_callback, args=(sel_p_idx,))
        else: st.info("No presets available.")

    c1, c2 = st.columns([0.6, 0.4])
    with c1:
        st.subheader(T["stg_header"])
        with st.form("stg"):
            cc1, cc2 = st.columns(2)
            with cc1: o = st.selectbox(T["col_origin"], LOC_CODES, format_func=lambda x: format_option(x, st.session_state.loc_map))
            with cc2: d = st.selectbox(T["col_dest"], LOC_CODES, index=1, format_func=lambda x: format_option(x, st.session_state.loc_map))
            cc3, cc4 = st.columns([0.7, 0.3])
            with cc3: i = st.selectbox(T["col_item"], ITEM_CODES, format_func=lambda x: format_option(x, st.session_state.item_map))
            with cc4: q = st.number_input(T["col_qty"], 1, value=10)
            if st.form_submit_button(T["stg_add"]):
                add_staging_task_callback(o, d, i, q); st.rerun()
        
        if st.session_state.staging_tasks:
            disp = [{"Origin": format_option(r['Origin'], st.session_state.loc_map), "Dest": format_option(r['Dest'], st.session_state.loc_map), "Item": format_option(r['Item'], st.session_state.item_map), "Qty": r['Qty']} for r in st.session_state.staging_tasks]
            
            edited_stg = st.data_editor(
                pd.DataFrame(disp), 
                num_rows="dynamic", 
                height=250, 
                key="staging_editor",
                column_config={
                    "Origin": st.column_config.SelectboxColumn(label=T["col_origin"], options=[format_option(c, st.session_state.loc_map) for c in LOC_CODES], required=True),
                    "Dest": st.column_config.SelectboxColumn(label=T["col_dest"], options=[format_option(c, st.session_state.loc_map) for c in LOC_CODES], required=True),
                    "Item": st.column_config.SelectboxColumn(label=T["col_item"], options=[format_option(c, st.session_state.item_map) for c in ITEM_CODES], required=True),
                    "Qty": st.column_config.NumberColumn(label=T["col_qty"], min_value=1)
                }
            )
            
            new_staging = []
            for row in edited_stg.to_dict('records'):
                new_staging.append({"Origin": parse_option(row["Origin"]), "Dest": parse_option(row["Dest"]), "Item": parse_option(row["Item"]), "Qty": safe_int(row.get("Qty"))})
            
            if new_staging != st.session_state.staging_tasks:
                 st.session_state.staging_tasks = new_staging; st.rerun()
            
            st.button("🗑️ " + T["calc_reset"], on_click=clear_staging_callback)
        else: st.info(T["stg_empty"])

    with c2:
        st.subheader(T["calc_header"])
        c_name = st.text_input(T["name_label"], placeholder=T["name_placeholder"], key="contract_name_input")
        st.markdown(f"### {int(st.session_state.calc_value):,} aUEC")
        
        def add(n): st.session_state.calc_value = str(n) if st.session_state.calc_value=="0" else st.session_state.calc_value+str(n)
        def back(): st.session_state.calc_value = st.session_state.calc_value[:-1] if len(st.session_state.calc_value)>1 else "0"
        
        k1, k2, k3 = st.columns(3)
        with k1: 
            if st.button("7", use_container_width=True): add(7); st.rerun()
            if st.button("4", use_container_width=True): add(4); st.rerun()
            if st.button("1", use_container_width=True): add(1); st.rerun()
            if st.button("C", use_container_width=True): st.session_state.calc_value="0"; st.rerun()
        with k2:
            if st.button("8", use_container_width=True): add(8); st.rerun()
            if st.button("5", use_container_width=True): add(5); st.rerun()
            if st.button("2", use_container_width=True): add(2); st.rerun()
            if st.button("0", use_container_width=True): add(0); st.rerun()
        with k3:
            if st.button("9", use_container_width=True): add(9); st.rerun()
            if st.button("6", use_container_width=True): add(6); st.rerun()
            if st.button("3", use_container_width=True): add(3); st.rerun()
            if st.button("⌫", use_container_width=True): back(); st.rerun()

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button(T["save_btn"], use_container_width=True):
                if not st.session_state.staging_tasks: st.toast(T["warn_no_task"])
                else: save_preset_callback_tab1(); st.toast(f"Preset Saved!"); st.rerun()
        with col_act2:
            st.button(T["calc_commit"], type="primary", use_container_width=True, on_click=commit_contract_callback)

# Tab 2: Manage (Standard UI)
with tab2:
    with st.expander(T["preset_sec"]):
        if st.session_state.presets:
            p_opts = [f"{p.get('name','?')} ({len(p.get('tasks',[]))})" for p in st.session_state.presets]
            sel = st.selectbox("Preset", range(len(p_opts)), format_func=lambda x: p_opts[x])
            c_l, c_d = st.columns([0.8, 0.2])
            with c_l: st.button(T["load_btn"], on_click=load_preset_to_manage_callback, args=(sel,))
            with c_d: st.button(T["del_preset"], on_click=delete_preset_callback, args=(sel,))
        else: st.info("Empty")

    st.divider()
    st.subheader(T["grp_manage"])
    for idx, grp in enumerate(st.session_state.mission_groups):
        with st.expander(f"📜 {grp['name']} | 💰 {grp['reward']:,}"):
            c1, c2 = st.columns([0.7, 0.3])
            c1.text_input(T["edit_name"], value=grp['name'], key=f"gn_{idx}", on_change=update_group_name_callback, args=(idx, f"gn_{idx}"))
            c2.number_input(T["edit_reward"], value=grp['reward'], key=f"gr_{idx}", on_change=update_group_reward_callback, args=(idx, f"gr_{idx}"))
            
            disp = [{"Origin": format_option(r['Origin'], st.session_state.loc_map), "Dest": format_option(r['Dest'], st.session_state.loc_map), "Item": format_option(r['Item'], st.session_state.item_map), "Qty": r['Qty']} for r in grp['tasks']]
            
            edited_grp_df = st.data_editor(
                pd.DataFrame(disp), 
                num_rows="dynamic", 
                key=f"gedit_{idx}",
                column_config={
                    "Origin": st.column_config.SelectboxColumn(label=T["col_origin"], options=[format_option(c, st.session_state.loc_map) for c in LOC_CODES], required=True),
                    "Dest": st.column_config.SelectboxColumn(label=T["col_dest"], options=[format_option(c, st.session_state.loc_map) for c in LOC_CODES], required=True),
                    "Item": st.column_config.SelectboxColumn(label=T["col_item"], options=[format_option(c, st.session_state.item_map) for c in ITEM_CODES], required=True),
                    "Qty": st.column_config.NumberColumn(label=T["col_qty"], min_value=1)
                }
            )
            
            updated_tasks = []
            for row in edited_grp_df.to_dict('records'):
                updated_tasks.append({"Origin": parse_option(row["Origin"]), "Dest": parse_option(row["Dest"]), "Item": parse_option(row["Item"]), "Qty": safe_int(row.get("Qty"))})
            
            if updated_tasks != grp.get('tasks', []):
                st.session_state.mission_groups[idx]['tasks'] = updated_tasks; st.rerun()
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button(T["save_btn"], key=f"sv_{idx}"):
                    save_preset_callback_tab2(idx); st.toast("Preset Saved!"); st.rerun() 
            with c2:
                st.button(T["grp_del"], key=f"dl_{idx}", on_click=delete_group_callback, args=(idx,))

    st.button(T["clear_btn"], on_click=clear_all_callback)

# Tab 3: Sim
with tab3:
    flat = flatten_groups(st.session_state.mission_groups)
    if flat:
        c1, c2 = st.columns([0.7, 0.3])
        locs = sorted(list(set([t['Origin'] for t in flat] + [t['Dest'] for t in flat])))
        with c1: sl = st.selectbox(T["start_loc"], locs, format_func=lambda x: format_option(x, st.session_state.loc_map))
        with c2: rt = st.checkbox(T["return_start"], True)
        
        with st.expander(T["adv_opt"]):
            c1, c2 = st.columns(2)
            with c1: ff = st.multiselect(T["opt_first"], locs, format_func=lambda x: format_option(x, st.session_state.loc_map))
            with c2: fl = st.multiselect(T["opt_last"], locs, format_func=lambda x: format_option(x, st.session_state.loc_map))

        if st.button(T["calc_btn"], type="primary", use_container_width=True):
            with st.spinner("..."):
                paths = find_smart_paths(flat, sl, ff, fl, rt)
                st.session_state.found_routes = []
                seen = set()
                for p in paths:
                    s = " -> ".join(p)
                    if s not in seen:
                        seen.add(s); st.session_state.found_routes.append(p)
                if st.session_state.found_routes: st.toast(f"Found {len(st.session_state.found_routes)}")
                else: st.warning("No routes")

        st.divider()
        if st.session_state.found_routes:
            opts = [" ➔ ".join([get_loc_label(x) for x in p]) for p in st.session_state.found_routes]
            sel_idx = st.radio(T["select_route"], range(len(opts)), format_func=lambda x: opts[x])
            path = st.session_state.found_routes[sel_idx]
            
            pending = copy.deepcopy(flat)
            onboard = []
            cur_max = 0
            
            for stop in path:
                s_n = get_loc_label(stop)
                u_str = ""; l_str = ""
                rem_onboard = []
                for i in onboard:
                    if i['Dest'] == stop: u_str += f"{get_item_label(i['Item'])}({i['Qty']}) "
                    else: rem_onboard.append(i)
                onboard = rem_onboard
                
                rem_pending = []
                for i in pending:
                    if i['Origin'] == stop:
                        onboard.append(i)
                        l_str += f"{get_item_label(i['Item'])}({i['Qty']}->{get_loc_label(i['Dest'])}) "
                    else: rem_pending.append(i)
                pending = rem_pending
                
                cur = sum(x['Qty'] for x in onboard)
                cur_max = max(cur_max, cur)
                
                with st.expander(f"📍 **{s_n}** (Cargo: {cur})", expanded=True):
                    if u_str: st.markdown(f":orange[**🔻 {T['unload']}**] {u_str}")
                    if l_str: st.markdown(f":green[**🔺 {T['load']}**] {l_str}")
            
            st.markdown("---")
            # [FIX v0.27.10] Variable name fix
            if cur_max > capa_val: st.error(f"{T['overload']} {cur_max}/{capa_str}")
            else: st.success(f"{T['success']} Max: {cur_max}/{capa_str}")

    else: st.info("Empty")

# --- Footer ---
st.divider()
footer_html = f"""
<div style='text-align: center; font-size: 0.8rem; color: #666;'>
    <p>
        {T['footer_plan']}: <a href='https://robertsspaceindustries.com/en/citizens/MeloPugna' target='_blank' style='text-decoration: none; color: #00D4FF;'>MeloPugna</a>
        &nbsp; | &nbsp;
        {T['footer_code']}: <a href='https://deepmind.google/technologies/gemini/' target='_blank' style='text-decoration: none; color: #00D4FF;'>Google Gemini</a>
    </p>
    <p style='font-size: 0.7rem; margin-top: -10px;'>{T['footer_ai_notice']}</p>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)