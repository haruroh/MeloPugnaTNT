import streamlit as st
import copy
import math
from utils.logic import flatten_groups, format_option, find_smart_paths, get_loc_label, get_item_label

def render_tab3(T, loc_codes, capa_val, capa_str):
    flat = flatten_groups(st.session_state.mission_groups)
    
    if flat:
        c1, c2 = st.columns([0.7, 0.3])
        # 전체 방문해야 할 모든 장소 추출
        all_stops = sorted(list(set([t['Origin'] for t in flat] + [t['Dest'] for t in flat])))
        
        with c1: 
            sl = st.selectbox(T["start_loc"], all_stops, format_func=lambda x: format_option(x, st.session_state.loc_map))
        with c2: 
            rt = st.checkbox(T["return_start"], True)
        
        # 고급 설정 (강제로 열리게 할 수도 있음)
        with st.expander(T["adv_opt"], expanded=False):
            ac1, ac2 = st.columns(2)
            with ac1: 
                ff = st.multiselect(T["opt_first"], all_stops, format_func=lambda x: format_option(x, st.session_state.loc_map))
            with ac2: 
                fl = st.multiselect(T["opt_last"], all_stops, format_func=lambda x: format_option(x, st.session_state.loc_map))

        # --- [안전장치 로직 시작] ---
        # 계산해야 할 '중간 경유지' 개수 미리 파악
        fixed_locs = {sl} | set(ff) | set(fl)
        middle_locs = [l for l in all_stops if l not in fixed_locs]
        complexity = len(middle_locs)
        
        # 기준: 중간 경유지가 8개 이상이면 계산 금지 (8! = 40,320회 연산, 9!부터는 36만회로 급증)
        THRESHOLD = 8 
        
        if st.button(T["calc_btn"], type="primary", use_container_width=True):
            if complexity >= THRESHOLD:
                st.error(f"⚠️ **탐색할 경유지가 너무 많습니다! ({complexity}곳)**")
                st.warning(f"""
                연산량이 너무 많아 시스템이 응답하지 않을 수 있습니다.
                **[고급 설정]**을 열어 **'첫 경유지'** 또는 **'마지막 경유지'**를 지정하여 탐색 범위를 줄여주세요.
                (권장: 자동 탐색 구간 {THRESHOLD-1}곳 이하)
                """)
            else:
                with st.spinner("Calculating optimal routes..."):
                    # 실제 계산 로직 (기존과 동일)
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
        
        # --- 결과 표시 로직 (기존과 동일) ---
        st.divider()
        if st.session_state.found_routes:
            # 상위 5개만 보여주거나, 라디오 버튼으로 선택
            opts = [f"Route {i+1}: {' ➔ '.join([get_loc_label(x, st.session_state.loc_map) for x in p])}" for i, p in enumerate(st.session_state.found_routes)]
            
            # 너무 길면 보기 힘드니까 경로 요약해서 보여주기
            sel_idx = st.radio(T["select_route"], range(len(opts)), format_func=lambda x: opts[x])
            
            path = st.session_state.found_routes[sel_idx]
            
            # 시뮬레이션 상세 출력
            pending = copy.deepcopy(flat)
            onboard = []
            cur_max = 0
            
            for stop in path:
                s_n = get_loc_label(stop, st.session_state.loc_map)
                u_str = ""
                l_str = ""
                
                # 하차 (Unload)
                rem_onboard = []
                for i in onboard:
                    if i['Dest'] == stop: 
                        u_str += f"{get_item_label(i['Item'], st.session_state.item_map)}({i['Qty']}) "
                    else: 
                        rem_onboard.append(i)
                onboard = rem_onboard
                
                # 상차 (Load)
                rem_pending = []
                for i in pending:
                    if i['Origin'] == stop:
                        onboard.append(i)
                        l_str += f"{get_item_label(i['Item'], st.session_state.item_map)}({i['Qty']}->{get_loc_label(i['Dest'], st.session_state.loc_map)}) "
                    else: 
                        rem_pending.append(i)
                pending = rem_pending
                
                cur = sum(x['Qty'] for x in onboard)
                cur_max = max(cur_max, cur)
                
                # 카드 형태로 단계별 표시
                with st.expander(f"📍 **{s_n}** (Cargo: {cur} SCU)", expanded=True):
                    if u_str: st.markdown(f":orange[**🔻 {T['unload']}**] {u_str}")
                    if l_str: st.markdown(f":green[**🔺 {T['load']}**] {l_str}")
            
            st.markdown("---")
            if cur_max > capa_val: 
                st.error(f"{T['overload']} {cur_max} / {capa_str}")
            else: 
                st.success(f"{T['success']} Max Load: {cur_max} / {capa_str}")

    else: 
        st.info("No tasks available to simulate.")