import streamlit as st
import pandas as pd
import copy
from utils.logic import format_option, parse_option, safe_int

def render_tab1(T, loc_codes, item_codes):
    with st.expander(T["tab1_preset"], expanded=False):
        if st.session_state.presets:
            p_opts = [f"{p.get('name','?')} ({len(p.get('tasks',[]))} tasks)" for p in st.session_state.presets]
            sel_p_idx = st.selectbox("Select Preset to Load", range(len(p_opts)), format_func=lambda x: p_opts[x], key="t1_preset_sel")
            
            def load_preset():
                loaded = copy.deepcopy(st.session_state.presets[sel_p_idx])
                st.session_state.staging_tasks = loaded['tasks']
                st.session_state.calc_value = str(loaded.get('reward', 0))
                st.session_state.contract_name_input = loaded.get('name', "")
                
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
            def save_preset():
                if not st.session_state.staging_tasks: return
                c_name = st.session_state.contract_name_input
                fn = c_name if c_name.strip() else f"Contract #{len(st.session_state.mission_groups)+1}"
                new_p = {"name": fn, "reward": int(st.session_state.calc_value), "tasks": copy.deepcopy(st.session_state.staging_tasks)}
                st.session_state.presets.append(new_p)
            
            if st.button(T["save_btn"], use_container_width=True):
                if not st.session_state.staging_tasks: st.toast(T["warn_no_task"])
                else: save_preset(); st.toast(f"Preset Saved!"); st.rerun()
        with col_act2:
            def commit():
                if not st.session_state.staging_tasks: return 
                c_name = st.session_state.contract_name_input
                fn = c_name if c_name.strip() else f"Contract #{len(st.session_state.mission_groups)+1}"
                grp = {"name": fn, "reward": int(st.session_state.calc_value), "tasks": copy.deepcopy(st.session_state.staging_tasks)}
                st.session_state.mission_groups.append(grp)
                st.session_state.staging_tasks = []; st.session_state.calc_value = "0"; st.session_state.contract_name_input = ""
            
            st.button(T["calc_commit"], type="primary", use_container_width=True, on_click=commit)