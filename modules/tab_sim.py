# modules/tab_sim.py

import streamlit as st
import copy
from utils.logic import flatten_groups, format_option, find_smart_paths, get_loc_label, get_item_label

def render_tab3(T, loc_codes, capa_val, capa_str):
    flat = flatten_groups(st.session_state.mission_groups)
    
    if flat:
        # ... (위쪽 코드: c1, c2 컬럼, 고급 설정, 버튼 등은 그대로 유지) ...
        c1, c2 = st.columns([0.7, 0.3])
        all_stops = sorted(list(set([t['Origin'] for t in flat] + [t['Dest'] for t in flat])))
        total_locs = len(all_stops)
        
        with c1: 
            sl = st.selectbox(T["start_loc"], all_stops, format_func=lambda x: format_option(x, st.session_state.loc_map))
        with c2: 
            rt = st.checkbox(T["return_start"], True)
        
        THRESHOLD = 7 
        if total_locs > THRESHOLD:
            st.warning(f"📍 **방문 예정지: 총 {total_locs}곳** (연산량 과다 예상)")
            
        with st.expander(T["adv_opt"], expanded=(total_locs > 7)):
            ac1, ac2 = st.columns(2)
            with ac1: ff = st.multiselect(T["opt_first"], all_stops, format_func=lambda x: format_option(x, st.session_state.loc_map))
            with ac2: fl = st.multiselect(T["opt_last"], all_stops, format_func=lambda x: format_option(x, st.session_state.loc_map))

        fixed_locs = {sl} | set(ff) | set(fl)
        middle_locs = [l for l in all_stops if l not in fixed_locs]
        complexity = len(middle_locs)
        
        if st.button(T["calc_btn"], type="primary", use_container_width=True):
            st.session_state.found_routes = []
            
            if complexity > THRESHOLD:
                st.error(f"**⛔ 탐색 불가: 중간 경유지가 너무 많습니다 ({THRESHOLD}곳)**")
                #st.warning(f"**시스템 보호를 위해 자동 탐색은 중간 경유지 {THRESHOLD}곳 이하일 때만 가능합니다.**")
                st.markdown(f"""
                시스템 보호를 위해 자동 탐색은 위의 **[고급 설정]**을 이용하여 **첫 경유지**나 **마지막 경유지**를 수동으로 지정해주세요.
                (현재 남은 자동 탐색 구간: **{complexity}**곳 → 목표: **{THRESHOLD}**곳 이하)
                """)
            else:
                with st.spinner("Calculating..."):
                    paths = find_smart_paths(flat, sl, ff, fl, rt)
                    seen = set()
                    for p in paths:
                        s = " -> ".join(p)
                        if s not in seen: seen.add(s); st.session_state.found_routes.append(p)
                    
                    if st.session_state.found_routes: 
                        # 토스트 메시지도 띄우지만, 이제 아래 라디오 버튼에 영구적으로 표시됨
                        st.toast(f"Found {len(st.session_state.found_routes)} Routes!", icon="✅")
                    else: 
                        st.warning("No routes found.")
        
        st.divider()
        if st.session_state.found_routes:
            opts = [f"Route {i+1}: {' ➔ '.join([get_loc_label(x, st.session_state.loc_map) for x in p])}" for i, p in enumerate(st.session_state.found_routes)]
            
            # 👇 [수정됨] 여기서 .format()을 사용해 숫자를 끼워넣습니다!
            route_count = len(st.session_state.found_routes)
            radio_label = T["select_route"].format(route_count)
            #print(T["select_route"])
            
            sel_idx = st.radio(radio_label, range(len(opts)), format_func=lambda x: opts[x])
            path = st.session_state.found_routes[sel_idx]
            
            # ... (아래쪽 시뮬레이션 상세 표시 로직은 그대로 유지) ...
            pending = copy.deepcopy(flat)
            onboard = []
            cur_max = 0
            
            for stop in path:
                s_n = get_loc_label(stop, st.session_state.loc_map)
                
                unload_msgs = []
                rem_onboard = []
                for i in onboard:
                    if i['Dest'] == stop: 
                        item_name = get_item_label(i['Item'], st.session_state.item_map)
                        origin_name = get_loc_label(i['Origin'], st.session_state.loc_map)
                        mission_name = i.get('Mission', 'Unknown')
                        msg = f"📦 **{item_name}** ({i['Qty']} SCU)\n&nbsp;&nbsp;&nbsp;&nbsp;└ 📜 {mission_name} (from {origin_name})"
                        unload_msgs.append(msg)
                    else: 
                        rem_onboard.append(i)
                onboard = rem_onboard
                
                l_str = ""
                rem_pending = []
                for i in pending:
                    if i['Origin'] == stop:
                        onboard.append(i)
                        l_str += f"{get_item_label(i['Item'], st.session_state.item_map)}({i['Qty']}->{get_loc_label(i['Dest'], st.session_state.loc_map)}) "
                    else: rem_pending.append(i)
                pending = rem_pending
                
                cur = sum(x['Qty'] for x in onboard)
                cur_max = max(cur_max, cur)
                
                with st.expander(f"📍 **{s_n}** (Cargo: {cur} SCU)", expanded=True):
                    if unload_msgs:
                        st.markdown(f":orange[**🔻 {T['unload']} (하차 목록)**]")
                        for m in unload_msgs:
                            st.info(m)
                            
                    if l_str: st.markdown(f":green[**🔺 {T['load']}**] {l_str}")
            
            st.markdown("---")
            if cur_max > capa_val: st.error(f"{T['overload']} {cur_max} / {capa_str}")
            else: st.success(f"{T['success']} Max Load: {cur_max} / {capa_str}")

    else: st.info("No tasks available.")