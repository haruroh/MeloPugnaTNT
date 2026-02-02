import streamlit as st
import pandas as pd
import copy
from utils.logic import format_option, parse_option, safe_int

def render_tab1(T, loc_codes, item_codes):
    # CSS 유지
    st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"]:has(span#calc-marker) > div[data-testid="stHorizontalBlock"] {
        flex-direction: row !important; flex-wrap: nowrap !important; gap: 0.5rem !important;
    }
    div[data-testid="stVerticalBlock"]:has(span#calc-marker) > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: auto !important; flex: 1 1 0px !important; min-width: 0px !important;
    }
    div[data-testid="stVerticalBlock"]:has(span#calc-marker) button {
        width: 100% !important; padding: 0.25rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.expander(T["tab1_preset"], expanded=False):
        if st.session_state.presets:
            p_opts = [f"{p.get('name','?')} ({len(p.get('tasks',[]))} tasks)" for p in st.session_state.presets]
            sel_p_idx = st.selectbox("Select Preset to Load", range(len(p_opts)), format_func=lambda x: p_opts[x], key="t1_preset_sel")
            
            def load_preset():
                loaded = copy.deepcopy(st.session_state.presets[sel_p_idx])
                st.session_state.staging_tasks = loaded['tasks']
                
                # 값 동기화
                reward_val = loaded.get('reward', 0)
                st.session_state.calc_value = str(reward_val)
                st.session_state.manual_reward_input = int(reward_val)
                
                st.session_state.contract_name_input = loaded.get('name', "")
                st.session_state.found_routes = []
                
            st.button(T["load_btn"], key="t1_load_btn", on_click=load_preset)
        else: st.info("No presets available.")

    c1, c2 = st.columns([0.6, 0.4])
    with c1:
        st.subheader(T["stg_header"])
        with st.form("stg"):
            cc1, cc2 = st.columns(2)
            with cc1: o = st.selectbox(T["col_origin"], loc_codes, format_func=lambda x: format_option(x, st.session_state.loc_map))
            with cc2: d = st.selectbox(T["col_dest"], loc_codes, index=1, format_func=lambda x: format_option(x, st.session_state.loc_map))
            cc3, cc4 = st.columns([0.7, 0.3])
            with cc3: i = st.selectbox(T["col_item"], item_codes, format_func=lambda x: format_option(x, st.session_state.item_map))
            with cc4: q = st.number_input(T["col_qty"], 1, value=10)
            if st.form_submit_button(T["stg_add"]):
                st.session_state.staging_tasks.append({"Origin": o, "Dest": d, "Item": i, "Qty": int(q)})
                st.rerun()
        
        if st.session_state.staging_tasks:
            disp = [{"Origin": format_option(r['Origin'], st.session_state.loc_map), "Dest": format_option(r['Dest'], st.session_state.loc_map), "Item": format_option(r['Item'], st.session_state.item_map), "Qty": r['Qty']} for r in st.session_state.staging_tasks]
            
            edited_stg = st.data_editor(
                pd.DataFrame(disp), 
                num_rows="dynamic", 
                height=250, 
                key="staging_editor",
                column_config={
                    "Origin": st.column_config.SelectboxColumn(label=T["col_origin"], options=[format_option(c, st.session_state.loc_map) for c in loc_codes], required=True),
                    "Dest": st.column_config.SelectboxColumn(label=T["col_dest"], options=[format_option(c, st.session_state.loc_map) for c in loc_codes], required=True),
                    "Item": st.column_config.SelectboxColumn(label=T["col_item"], options=[format_option(c, st.session_state.item_map) for c in item_codes], required=True),
                    "Qty": st.column_config.NumberColumn(label=T["col_qty"], min_value=1)
                }
            )
            new_staging = []
            for row in edited_stg.to_dict('records'):
                new_staging.append({"Origin": parse_option(row["Origin"]), "Dest": parse_option(row["Dest"]), "Item": parse_option(row["Item"]), "Qty": safe_int(row.get("Qty"))})
            
            if new_staging != st.session_state.staging_tasks:
                 st.session_state.staging_tasks = new_staging; st.rerun()
            
            def clear_stg(): st.session_state.staging_tasks = []
            st.button("🗑️ " + T["calc_reset"], on_click=clear_stg)
        else: st.info(T["stg_empty"])

    with c2:
        st.subheader(T["calc_header"])
        st.text_input(T["name_label"], placeholder=T["name_placeholder"], key="contract_name_input")
        
        # 👇 [수정됨 1] 입력창이 비었을 때(None) "0"으로 처리하는 안전장치 추가
        def sync_input():
            val = st.session_state.manual_reward_input
            if val is None:
                st.session_state.calc_value = "0"
            else:
                st.session_state.calc_value = str(val)

        # 👇 [수정됨 2] 계산기 버튼용 콜백 (State -> Input)
        def update_both(new_val_str):
            st.session_state.calc_value = new_val_str
            # 문자열이 비어있거나 이상하면 0으로 처리
            st.session_state.manual_reward_input = int(safe_int(new_val_str))

        def cb_add(n):
            current = st.session_state.calc_value
            # current가 None 문자열이면 "0"으로 취급
            if current == "None" or current is None: current = "0"
            
            new_val = str(n) if current == "0" else current + str(n)
            update_both(new_val)

        def cb_back():
            current = st.session_state.calc_value
            if current == "None" or current is None: current = "0"
            
            new_val = current[:-1] if len(current) > 1 else "0"
            update_both(new_val)
        
        def cb_clear():
            update_both("0")

        # 초기값 안전 장치
        if "manual_reward_input" not in st.session_state:
            st.session_state.manual_reward_input = int(safe_int(st.session_state.calc_value))

        # 숫자 입력창
        st.number_input(
            label="Reward (aUEC)", 
            value=None, 
            min_value=0, 
            step=1000, 
            key="manual_reward_input", 
            on_change=sync_input
        )
        
        # 계산기 버튼 영역
        with st.container():
            st.markdown('<span id="calc-marker"></span>', unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            with k1: 
                st.button("7", use_container_width=True, on_click=cb_add, args=(7,))
                st.button("4", use_container_width=True, on_click=cb_add, args=(4,))
                st.button("1", use_container_width=True, on_click=cb_add, args=(1,))
                st.button("C", use_container_width=True, on_click=cb_clear)
            with k2:
                st.button("8", use_container_width=True, on_click=cb_add, args=(8,))
                st.button("5", use_container_width=True, on_click=cb_add, args=(5,))
                st.button("2", use_container_width=True, on_click=cb_add, args=(2,))
                st.button("0", use_container_width=True, on_click=cb_add, args=(0,))
            with k3:
                st.button("9", use_container_width=True, on_click=cb_add, args=(9,))
                st.button("6", use_container_width=True, on_click=cb_add, args=(6,))
                st.button("3", use_container_width=True, on_click=cb_add, args=(3,))
                st.button("⌫", use_container_width=True, on_click=cb_back)

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            def save_preset():
                if not st.session_state.staging_tasks: return
                c_name = st.session_state.contract_name_input
                fn = c_name if c_name.strip() else f"Contract #{len(st.session_state.mission_groups)+1}"
                final_reward = safe_int(st.session_state.manual_reward_input) # 안전하게 변환
                new_p = {"name": fn, "reward": final_reward, "tasks": copy.deepcopy(st.session_state.staging_tasks)}
                st.session_state.presets.append(new_p)
            
            if st.button(T["save_btn"], use_container_width=True):
                if not st.session_state.staging_tasks: st.toast(T["warn_no_task"])
                else: save_preset(); st.toast(f"Preset Saved!"); st.rerun()
        with col_act2:
            def commit():
                if not st.session_state.staging_tasks: return 
                c_name = st.session_state.contract_name_input
                fn = c_name if c_name.strip() else f"Contract #{len(st.session_state.mission_groups)+1}"
                final_reward = safe_int(st.session_state.manual_reward_input) # 안전하게 변환
                grp = {"name": fn, "reward": final_reward, "tasks": copy.deepcopy(st.session_state.staging_tasks)}
                st.session_state.mission_groups.append(grp)
                
                # 초기화
                st.session_state.staging_tasks = []
                update_both("0") 
                st.session_state.contract_name_input = ""
                st.session_state.found_routes = []
            
            st.button(T["calc_commit"], type="primary", use_container_width=True, on_click=commit)