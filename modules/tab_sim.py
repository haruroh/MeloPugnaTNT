import streamlit as st
import copy
from utils.logic import flatten_groups, format_option, find_smart_paths, get_loc_label, get_item_label

def render_tab3(T, loc_codes, capa_val, capa_str):
    flat = flatten_groups(st.session_state.mission_groups)
    
    if flat:
        c1, c2 = st.columns([0.7, 0.3])
        # 전체 방문해야 할 모든 장소 추출
        all_stops = sorted(list(set([t['Origin'] for t in flat] + [t['Dest'] for t in flat])))
        total_locs = len(all_stops) # 총 경유지 개수
        
        with c1: 
            sl = st.selectbox(T["start_loc"], all_stops, format_func=lambda x: format_option(x, st.session_state.loc_map))
        with c2: 
            rt = st.checkbox(T["return_start"], True)
        
        # [NEW] 현재 경유지 상태 브리핑
        if total_locs > 7:
            st.warning(f"📍 **방문 예정지: 총 {total_locs}곳** (연산량 과다 예상)")
            st.caption("💡 **팁:** 경유지가 8곳 이상이면 경로 탐색이 매우 오래 걸립니다. 아래 **[고급 설정]**에서 '첫 경유지'와 '마지막 경유지'를 지정하여 중간 탐색 구간을 줄여주세요.")
        else:
            st.info(f"📍 **방문 예정지: 총 {total_locs}곳** (탐색 가능)")

        # 고급 설정
        with st.expander(T["adv_opt"], expanded=(total_locs > 7)): # 많으면 자동으로 열어줌
            ac1, ac2 = st.columns(2)
            with ac1: 
                ff = st.multiselect(T["opt_first"], all_stops, format_func=lambda x: format_option(x, st.session_state.loc_map))
            with ac2: 
                fl = st.multiselect(T["opt_last"], all_stops, format_func=lambda x: format_option(x, st.session_state.loc_map))

        # 계산 가능 여부 체크
        fixed_locs = {sl} | set(ff) | set(fl)
        middle_locs = [l for l in all_stops if l not in fixed_locs]
        complexity = len(middle_locs)
        THRESHOLD = 8 
        
        if st.button(T["calc_btn"], type="primary", use_container_width=True):
            if complexity >= THRESHOLD:
                st.error(f"⛔ **탐색 불가: 중간 경유지가 너무 많습니다 ({complexity}곳)**")
                st.markdown(f"""
                시스템 보호를 위해 자동 탐색은 **중간 경유지 7곳 이하**일 때만 가능합니다.
                위의 **[고급 설정]**을 이용하여 **첫 경유지**나 **마지막 경유지**를 수동으로 지정해주세요.
                (현재 남은 자동 탐색 구간: **{complexity}**곳 → 목표: **{THRESHOLD-1}**곳 이하)
                """)
            else:
                with st.spinner("Calculating optimal routes..."):
                    paths = find_smart_paths(flat, sl, ff, fl, rt)
                    st.session_state.found_routes = []
                    seen = set()
                    for p in paths:
                        s = " -> ".join(p)
                        if s not in seen:
                            seen.add(s)
                            st.session_state.found_routes.append(p)
                    
                    if st.session_state.found_routes: 
                        st.toast(f"Found {len(st.session_state.found_routes)} Routes!", icon="✅")
                    else: 
                        st.warning("No valid routes found based on current tasks.")
        
        st.divider()
        if st.session_state.found_routes:
            opts = [f"Route {i+1}: {' ➔ '.join([get_loc_label(x, st.session_state.loc_map) for x in p])}" for i, p in enumerate(st.session_state.found_routes)]
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
                
                with st.expander(f"📍 **{s_n}** (Cargo: {cur} SCU)", expanded=True):
                    if u_str: st.markdown(f":orange[**🔻 {T['unload']}**] {u_str}")
                    if l_str: st.markdown(f":green[**🔺 {T['load']}**] {l_str}")
            
            st.markdown("---")
            if cur_max > capa_val: st.error(f"{T['overload']} {cur_max} / {capa_str}")
            else: st.success(f"{T['success']} Max Load: {cur_max} / {capa_str}")

    else: st.info("No tasks available to simulate.")