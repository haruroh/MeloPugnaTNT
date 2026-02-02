import streamlit as st
import json
from datetime import datetime
from utils.constants import generate_loc_code, generate_item_code
from utils.data_manager import get_sample_files, load_sample_file

def render_sidebar(T, fleet_mgr, master_db, db_status, loc_codes, item_codes):
    st.sidebar.title(T["sidebar_title"])
    if db_status.startswith("❌"): st.sidebar.error(f"DB: {db_status}")
    else: st.sidebar.caption(f"DB: {db_status}")
    
    uploaded = st.sidebar.file_uploader(T["upload_label"], type=["json"])
    if uploaded:
        file_id = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.processed_file_id != file_id:
            try:
                d = json.load(uploaded)
                if "loc_map" in d: 
                    st.session_state.loc_map = d["loc_map"]
                    for k, v in d["loc_map"].items(): st.session_state[f"l_{k}"] = v
                if "item_map" in d: 
                    st.session_state.item_map = d["item_map"]
                    for k, v in d["item_map"].items(): st.session_state[f"i_{k}"] = v
                if "mission_groups" in d: st.session_state.mission_groups = d["mission_groups"]
                if "presets" in d: st.session_state.presets = d["presets"]
                if "my_fleet" in d: fleet_mgr.update_fleet_from_upload(d["my_fleet"])
                if "current_ship_id" in d:
                    if fleet_mgr.get_ship_by_id(d["current_ship_id"]):
                        st.session_state.current_ship_id = d["current_ship_id"]
                    else:
                        all_s = fleet_mgr.get_all_options()
                        if all_s: st.session_state.current_ship_id = all_s[0]["id"]
                
                # [NEW] 파일 로드 시 이전 시뮬레이션 결과 초기화
                st.session_state.found_routes = []
                
                st.session_state.processed_file_id = file_id
                st.toast("File Loaded!", icon="✅")
                st.rerun() 
            except Exception as e: st.sidebar.error(f"Load Failed: {e}")

    sample_files = get_sample_files()
    if sample_files:
        with st.sidebar.expander("📂 Load Sample Data"):
            selected_sample = st.selectbox("Select Mission", sample_files)
            if st.button("Load Sample", use_container_width=True):
                d = load_sample_file(selected_sample)
                if d:
                    if "loc_map" in d: 
                        st.session_state.loc_map = d["loc_map"]
                        for k, v in d["loc_map"].items(): st.session_state[f"l_{k}"] = v
                    if "item_map" in d: 
                        st.session_state.item_map = d["item_map"]
                        for k, v in d["item_map"].items(): st.session_state[f"i_{k}"] = v
                    if "mission_groups" in d: st.session_state.mission_groups = d["mission_groups"]
                    if "presets" in d: st.session_state.presets = d["presets"]
                    if "my_fleet" in d: fleet_mgr.update_fleet_from_upload(d["my_fleet"])
                    if "current_ship_id" in d:
                        if fleet_mgr.get_ship_by_id(d["current_ship_id"]):
                            st.session_state.current_ship_id = d["current_ship_id"]
                        else:
                            all_s = fleet_mgr.get_all_options()
                            if all_s: st.session_state.current_ship_id = all_s[0]["id"]
                    
                    # [NEW] 샘플 로드 시에도 초기화
                    st.session_state.found_routes = []
                    
                    st.toast(f"Sample '{selected_sample}' Loaded!", icon="✅")
                    st.rerun()

    st.sidebar.divider()
    save_name = st.sidebar.text_input(T["save_filename_label"], value=f"melo_config_{datetime.now().strftime('%Y%m%d')}.json")
    st.sidebar.caption(T["save_path_info"])
    
    ex_data = {
        "current_ship_id": st.session_state.current_ship_id,
        "loc_map": st.session_state.loc_map, "item_map": st.session_state.item_map,
        "mission_groups": st.session_state.mission_groups, "presets": st.session_state.presets,
        "my_fleet": fleet_mgr.get_all_options() 
    }
    st.sidebar.download_button(label=T["download_label"], data=json.dumps(ex_data, indent=4, ensure_ascii=False), file_name=save_name, mime="application/json", use_container_width=True)
    
    st.sidebar.divider()
    lang_opt = st.sidebar.selectbox(T["lang_select"], ["KR", "EN"], index=["KR", "EN"].index(st.session_state.current_lang))
    
    my_ships = fleet_mgr.get_all_options()
    s_opts = {s["id"]: f"{s['model']} [{s['man']}] ({s['capa']} SCU)" for s in my_ships}
    
    def update_ship(): pass 
    if st.session_state.current_ship_id not in s_opts:
        if my_ships: st.session_state.current_ship_id = my_ships[0]["id"]
    
    st.sidebar.selectbox(T["ship_select"], options=list(s_opts.keys()), format_func=lambda x: s_opts[x], key="current_ship_id", on_change=update_ship)
    
    if st.session_state.current_lang != lang_opt:
        st.session_state.current_lang = lang_opt; st.rerun()

    with st.sidebar.expander(T["ship_add_expander"]):
        if not master_db: st.warning(T["master_db_missing"])
        else:
            search_term = st.text_input(T["ship_search_label"])
            if search_term: filtered_master = [m for m in master_db.keys() if search_term.lower() in m.lower()]
            else: filtered_master = sorted(list(master_db.keys()))
            target_model = st.selectbox("Model", filtered_master)
            if target_model:
                spec = master_db[target_model]
                st.caption(T["ship_info"].format(spec.get('name', target_model), spec.get('cargo', 0)))
                def add_ship_cb():
                    success, msg = fleet_mgr.add_ship_from_master(target_model, master_db)
                    if success: st.toast(msg, icon="🚀")
                    else: st.error(msg)
                st.button(T["ship_add_btn"], use_container_width=True, on_click=add_ship_cb)
    
    if len(my_ships) > 1:
        def del_ship_cb():
            res, msg = fleet_mgr.delete_ship(st.session_state.current_ship_id)
            if res:
                all_s = fleet_mgr.get_all_options(); st.session_state.current_ship_id = all_s[0]["id"]; st.toast(msg)
            else: st.error(msg)
        st.sidebar.button(T["ship_del_btn"], type="secondary", use_container_width=True, on_click=del_ship_cb)

    st.sidebar.divider()
    with st.sidebar.expander(T["map_expander"]):
        t1, t2 = st.tabs(["Loc", "Item"])
        with t1:
            for c in loc_codes: st.session_state.loc_map[c] = st.text_input(c, st.session_state.loc_map[c], key=f"l_{c}")
            c1, c2, c3 = st.columns(3)
            def add_loc():
                curr = len(st.session_state.loc_map); 
                if curr<50: st.session_state.loc_map[generate_loc_code(curr)] = ""; st.rerun()
            def clear_loc():
                for k in st.session_state.loc_map: st.session_state.loc_map[k] = ""; st.session_state[f"l_{k}"] = ""
                st.rerun()
            c1.button(T["add_loc_btn"], on_click=add_loc, use_container_width=True, key="btn_add_loc")
            c2.button(T["clear_loc_btn"], on_click=clear_loc, use_container_width=True, key="btn_clear_loc")
        with t2:
            for c in item_codes: st.session_state.item_map[c] = st.text_input(c, st.session_state.item_map[c], key=f"i_{c}")
            c1, c2, c3 = st.columns(3)
            def add_item():
                curr = len(st.session_state.item_map); 
                if curr<50: st.session_state.item_map[generate_item_code(curr)] = ""; st.rerun()
            def clear_item():
                for k in st.session_state.item_map: st.session_state.item_map[k] = ""; st.session_state[f"i_{k}"] = ""
                st.rerun()
            c1.button(T["add_item_btn"], on_click=add_item, use_container_width=True, key="btn_add_item")
            c2.button(T["clear_item_btn"], on_click=clear_item, use_container_width=True, key="btn_clear_item")
            
    st.sidebar.divider()
    if st.sidebar.button("💥 공장 초기화 (Reset All)", type="primary"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.cache_data.clear()
        st.rerun()