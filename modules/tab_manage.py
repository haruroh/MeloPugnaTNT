import streamlit as st
import pandas as pd
import copy
from utils.logic import format_option, parse_option, safe_int

def render_tab2(T, loc_codes, item_codes):
    with st.expander(T["preset_sec"]):
        if st.session_state.presets:
            p_opts = [f"{p.get('name','?')} ({len(p.get('tasks',[]))})" for p in st.session_state.presets]
            sel = st.selectbox("Preset", range(len(p_opts)), format_func=lambda x: p_opts[x])
            c_l, c_d = st.columns([0.8, 0.2])
            
            def load_p(): st.session_state.mission_groups.append(copy.deepcopy(st.session_state.presets[sel]))
            def del_p(): st.session_state.presets.pop(sel)
            
            with c_l: st.button(T["load_btn"], on_click=load_p)
            with c_d: st.button(T["del_preset"], on_click=del_p)
        else: st.info("Empty")

    st.divider()
    st.subheader(T["grp_manage"])
    
    # Callback wrappers need to be defined outside loop or handle index carefully
    def update_name(idx, k): st.session_state.mission_groups[idx]['name'] = st.session_state[k]
    def update_reward(idx, k): st.session_state.mission_groups[idx]['reward'] = int(st.session_state[k])
    def del_grp(idx): st.session_state.mission_groups.pop(idx)
    def save_grp(idx): 
        grp = st.session_state.mission_groups[idx]
        st.session_state.presets.append(copy.deepcopy(grp))

    for idx, grp in enumerate(st.session_state.mission_groups):
        with st.expander(f"📜 {grp['name']} | 💰 {grp['reward']:,}"):
            c1, c2 = st.columns([0.7, 0.3])
            c1.text_input(T["edit_name"], value=grp['name'], key=f"gn_{idx}", on_change=update_name, args=(idx, f"gn_{idx}"))
            c2.number_input(T["edit_reward"], value=grp['reward'], key=f"gr_{idx}", on_change=update_reward, args=(idx, f"gr_{idx}"))
            
            disp = [{"Origin": format_option(r['Origin'], st.session_state.loc_map), "Dest": format_option(r['Dest'], st.session_state.loc_map), "Item": format_option(r['Item'], st.session_state.item_map), "Qty": r['Qty']} for r in grp['tasks']]
            
            edited_grp_df = st.data_editor(
                pd.DataFrame(disp), 
                num_rows="dynamic", 
                key=f"gedit_{idx}",
                column_config={
                    "Origin": st.column_config.SelectboxColumn(label=T["col_origin"], options=[format_option(c, st.session_state.loc_map) for c in loc_codes], required=True),
                    "Dest": st.column_config.SelectboxColumn(label=T["col_dest"], options=[format_option(c, st.session_state.loc_map) for c in loc_codes], required=True),
                    "Item": st.column_config.SelectboxColumn(label=T["col_item"], options=[format_option(c, st.session_state.item_map) for c in item_codes], required=True),
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
                    save_grp(idx); st.toast("Preset Saved!"); st.rerun() 
            with c2:
                st.button(T["grp_del"], key=f"dl_{idx}", on_click=del_grp, args=(idx,))

    def clear_all(): st.session_state.mission_groups = []
    st.button(T["clear_btn"], on_click=clear_all)