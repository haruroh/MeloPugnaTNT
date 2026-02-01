import math
import itertools
import streamlit as st

def safe_int(val):
    try: return int(float(val)) if val is not None and not (isinstance(val, float) and (math.isnan(val) or math.isinf(val))) else 0
    except: return 0

def format_option(code, map_dict):
    name = map_dict.get(code, "")
    return f"{name} ({code})" if name else code

def parse_option(formatted_str):
    if "(" in formatted_str and formatted_str.endswith(")"): return formatted_str.split("(")[-1].strip(")")
    return formatted_str

def get_loc_label(code, loc_map): return loc_map.get(code, code)
def get_item_label(code, item_map): return item_map.get(code, code)

# 👇 [수정됨] 화물마다 'Mission' 이름표를 붙여줍니다!
def flatten_groups(groups):
    flat = []
    for g in groups:
        m_name = g.get('name', 'Unknown') # 계약 이름 가져오기
        for t in g.get('tasks', []):
            t_safe = t.copy()
            t_safe['Qty'] = safe_int(t.get('Qty', 0))
            t_safe['Mission'] = m_name    # 꼬리표 부착
            flat.append(t_safe)
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