import copy

# 코드 생성기
def generate_loc_code(n):
    if n < 26: return chr(65 + n)
    else: q, r = divmod(n, 26); return chr(64 + q) + chr(65 + r)

K_CORE = ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하"]
def generate_item_code(n):
    l = len(K_CORE)
    if n < l: return K_CORE[n]
    else: q, r = divmod(n, l); return K_CORE[q-1] + K_CORE[r]

# 기본값
PRESET_LOC_NAMES = ["Seraphim Station", "Orison", "Grim HEX", "Area18", "Baijini Point", "New Babbage", "Port Tressler", "Lorville", "Everus Harbor", "Pyrollis"]
PRESET_ITEM_NAMES = ["Medical Supplies", "Distilled Spirits", "Stims", "Processed Food", "Scrap", "RMC", "Gold", "Laranite", "Agricium", "Waste"]

DEFAULT_LOC_MAP = {generate_loc_code(i): (PRESET_LOC_NAMES[i] if i < len(PRESET_LOC_NAMES) else "") for i in range(26)}
DEFAULT_ITEM_MAP = {generate_item_code(i): (PRESET_ITEM_NAMES[i] if i < len(PRESET_ITEM_NAMES) else "") for i in range(14)}

DEFAULT_MISSIONS = [
    {"name": "💊 Seraphim Medical Run", "reward": 45000, "tasks": [{"Origin": "B", "Dest": "A", "Item": "가", "Qty": 10}, {"Origin": "A", "Dest": "C", "Item": "나", "Qty": 5}]}
]

INITIAL_FLEET = [
    {"id": "s_001", "man": "Drake Interplanetary", "model": "Cutlass Black", "capa": 46, "max_box": 16, "role": "Medium Freight", "size": "Medium", "pledge": "$110.00", "auec": "2,117,400 aUEC", "url": "https://www.spviewer.eu/performance?ship=drak_cutlass_black"},
]

RICH_DEFAULTS = {
    "language": "KR", "current_ship_id": "s_001",
    "loc_map": copy.deepcopy(DEFAULT_LOC_MAP), "item_map": copy.deepcopy(DEFAULT_ITEM_MAP),
    "mission_groups": copy.deepcopy(DEFAULT_MISSIONS), "presets": [],
    "my_fleet": copy.deepcopy(INITIAL_FLEET)
}

# 번역 데이터
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
        "ship_add_expander": "🚀 Add Ship (Master DB)", "ship_search_label": "Search Model", 
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