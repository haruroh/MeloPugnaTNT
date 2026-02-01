import streamlit as st
import copy
from utils.logic import flatten_groups, format_option, find_smart_paths, get_loc_label, get_item_label

def render_tab3(T, loc_codes, capa_val, capa_str):
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
            opts = [" ➔ ".join([get_loc_label(x, st.session_state.loc_map) for x in p]) for p in st.session_state.found_routes]
            sel_idx = st.radio(T["select_route"], range(len(opts)), format_func=lambda x: opts[x])
            path = st.session_state.found_routes[sel_idx]
            
            pending = copy.deepcopy(flat)
            onboard = []
            cur_max = 0
            
            for stop in path:
                s_n = get_loc_label(stop, st.session_state.loc_map)
                u_str = ""; l_str = ""; rem_onboard = []
                for i in onboard:
                    if i['Dest'] == stop: u_str += f"{get_item_label(i['Item'], st.session_state.item_map)}({i['Qty']}) "
                    else: rem_onboard.append(i)
                onboard = rem_onboard
                
                rem_pending = []
                for i in pending:
                    if i['Origin'] == stop:
                        onboard.append(i)
                        l_str += f"{get_item_label(i['Item'], st.session_state.item_map)}({i['Qty']}->{get_loc_label(i['Dest'], st.session_state.loc_map)}) "
                    else: rem_pending.append(i)
                pending = rem_pending
                
                cur = sum(x['Qty'] for x in onboard)
                cur_max = max(cur_max, cur)
                
                with st.expander(f"📍 **{s_n}** (Cargo: {cur})", expanded=True):
                    if u_str: st.markdown(f":orange[**🔻 {T['unload']}**] {u_str}")
                    if l_str: st.markdown(f":green[**🔺 {T['load']}**] {l_str}")
            
            st.markdown("---")
            if cur_max > capa_val: st.error(f"{T['overload']} {cur_max}/{capa_str}")
            else: st.success(f"{T['success']} Max: {cur_max}/{capa_str}")

    else: st.info("Empty")