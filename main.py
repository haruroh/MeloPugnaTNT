import streamlit as st
import copy
from pathlib import Path

# 모듈 Import
from utils.constants import RICH_DEFAULTS, TRANS
# 👇 [중요] 여기 끝에 있던 ', MASTER_SHIP_DB'를 지웠습니다!
from utils.data_manager import load_master_ship_db, FleetManager 
from utils.logic import flatten_groups
from modules.sidebar import render_sidebar
from modules.tab_add import render_tab1
from modules.tab_manage import render_tab2
from modules.tab_sim import render_tab3
# 👇 [추가] 버전을 가져옵니다
from utils.version import __version__

# --- Page Config ---
st.set_page_config(
    page_title=f"MeloPugna Trade & Transport {__version__} (Modular)", 
    layout="wide", 
    initial_sidebar_state="auto"
)

# --- Session Initialization ---
if 'loc_map' not in st.session_state: st.session_state.loc_map = copy.deepcopy(RICH_DEFAULTS["loc_map"])
if 'item_map' not in st.session_state: st.session_state.item_map = copy.deepcopy(RICH_DEFAULTS["item_map"])
if 'mission_groups' not in st.session_state: st.session_state.mission_groups = copy.deepcopy(RICH_DEFAULTS["mission_groups"])
if 'presets' not in st.session_state: st.session_state.presets = copy.deepcopy(RICH_DEFAULTS["presets"])
if 'current_lang' not in st.session_state: st.session_state.current_lang = RICH_DEFAULTS["language"]
if 'current_ship_id' not in st.session_state: st.session_state.current_ship_id = RICH_DEFAULTS["current_ship_id"]
if 'my_fleet' not in st.session_state: st.session_state.my_fleet = copy.deepcopy(RICH_DEFAULTS["my_fleet"])

if 'staging_tasks' not in st.session_state: st.session_state.staging_tasks = []
if 'calc_value' not in st.session_state: st.session_state.calc_value = "0"
if 'contract_name_input' not in st.session_state: st.session_state.contract_name_input = ""
if 'found_routes' not in st.session_state: st.session_state.found_routes = []
if 'processed_file_id' not in st.session_state: st.session_state.processed_file_id = ""

if 'input_qty' not in st.session_state: st.session_state.input_qty = 10
if 'tab1_qty' not in st.session_state: st.session_state.tab1_qty = 10

# --- Load Data ---
# 👇 함수를 실행해서 변수에 담습니다 (Import 하는 게 아님)
MASTER_SHIP_DB, DB_STATUS = load_master_ship_db() 
fleet_mgr = FleetManager()

# --- Common Resources ---
LOC_CODES = list(st.session_state.loc_map.keys())
ITEM_CODES = list(st.session_state.item_map.keys())
T = TRANS[st.session_state.current_lang]

# --- UI Header ---
st.title(f"🚀 {T['app_title']} {__version__}")
st.caption(T['app_subtitle'])

# --- Render Sidebar ---
render_sidebar(T, fleet_mgr, MASTER_SHIP_DB, DB_STATUS, LOC_CODES, ITEM_CODES)

# --- HUD Logic ---
s_dat = fleet_mgr.get_ship_by_id(st.session_state.current_ship_id)
if not s_dat: s_dat = RICH_DEFAULTS["my_fleet"][0]

# HUD Calculation
capa_val = s_dat.get('capa', 0)
capa_str = f"{capa_val} {T['unit_scu']}"
flat_list = flatten_groups(st.session_state.mission_groups)
total_cargo = sum(task.get('Qty', 0) for task in flat_list)
total_rev = sum(g.get('reward',0) for g in st.session_state.mission_groups)

# HUD UI
st.markdown("""
<style>
.hud-container { background: linear-gradient(135deg, #1A1A24, #0D0D12); border-radius: 12px; padding: 25px 30px; border: 1px solid #333; border-left: 6px solid #00D4FF; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
.hud-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 5px; }
.hud-ship-name { color: #FFFFFF; font-size: 2.8rem; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
.hud-manufacturer { color: #AAAAAA; font-size: 1.2rem; font-weight: 500; font-style: italic; }
.hud-link a { color: #00D4FF; font-size: 0.85rem; text-decoration: none; opacity: 0.8; transition: opacity 0.3s; margin-left: 2px; }
.hud-link a:hover { opacity: 1; text-decoration: underline; color: #FFD700; }
.hud-info-row { display: flex; gap: 20px; margin-top: 15px; flex-wrap: wrap; }
.info-item { background: rgba(255, 255, 255, 0.05); padding: 8px 12px; border-radius: 6px; border: 1px solid #444; }
.info-label { font-size: 0.8rem; color: #888; display: block; margin-bottom: 2px; }
.info-value { font-size: 1.1rem; font-weight: 700; color: #00D4FF; }
.info-value.orange { color: #FFA500; }
.hud-stats-row { display: flex; align-items: center; gap: 40px; border-top: 1px solid #333; padding-top: 15px; margin-top: 20px; }
.stat-box { display: flex; flex-direction: column; }
.stat-label { font-size: 0.8rem; color: #aaa; letter-spacing: 1px; }
.stat-value { font-size: 1.5rem; color: #EEE; font-weight: 700; }
.stat-value.gold { color: #FFD700; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hud-container">
    <div class="hud-header">
        <span class="hud-ship-name">{s_dat.get('model')}</span>
        <span class="hud-manufacturer">{s_dat.get('man')}</span>
    </div>
    <div class="hud-link"><a href="{s_dat.get('url')}" target="_blank">{T['link_spviewer']}</a></div>
    <div class="hud-info-row">
        <div class="info-item"><span class="info-label">{T['hud_stat_capa']}</span><span class="info-value">{capa_str}</span></div>
        <div class="info-item"><span class="info-label">{T['hud_stat_role']}</span><span class="info-value orange">{s_dat.get('role')}</span></div>
        <div class="info-item"><span class="info-label">{T['hud_stat_size']}</span><span class="info-value">{s_dat.get('size')}</span></div>
        <div class="info-item"><span class="info-label">{T['hud_stat_pledge']}</span><span class="info-value">{s_dat.get('pledge')}</span></div>
        <div class="info-item"><span class="info-label">{T['hud_stat_auec']}</span><span class="info-value">{s_dat.get('auec')}</span></div>
    </div>
    <div class="hud-stats-row">
        <div class="stat-box"><span class="stat-label">{T['hud_metric_cargo']}</span><span class="stat-value">{total_cargo} {T['unit_scu']}</span></div>
        <div class="stat-box"><span class="stat-label">{T['hud_metric_contract']}</span><span class="stat-value">{len(st.session_state.mission_groups)} {T['unit_groups']}</span></div>
        <div class="stat-box"><span class="stat-label">{T['hud_metric_rev']}</span><span class="stat-value gold">{total_rev:,} aUEC</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Main Tabs ---
tab1, tab2, tab3 = st.tabs([T["tab_1"], T["tab_2"], T["tab_3"]])

with tab1: render_tab1(T, LOC_CODES, ITEM_CODES)
with tab2: render_tab2(T, LOC_CODES, ITEM_CODES)
with tab3: render_tab3(T, LOC_CODES, capa_val, capa_str)

# --- Footer ---
st.divider()
footer_html = f"""
<div style='text-align: center; font-size: 0.8rem; color: #666;'>
    <p>
        {T['footer_plan']}: <a href='https://robertsspaceindustries.com/en/citizens/MeloPugna' target='_blank' style='text-decoration: none; color: #00D4FF;'>MeloPugna</a>
        &nbsp; | &nbsp;
        {T['footer_code']}: <a href='https://deepmind.google/technologies/gemini/' target='_blank' style='text-decoration: none; color: #00D4FF;'>Google Gemini</a>
    </p>
    <p style='font-size: 0.7rem; margin-top: -10px;'>{T['footer_ai_notice']}</p>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)