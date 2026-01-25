import os
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------------------------------------
# [함수] HTML 소스에서 함선 정보 추출하는 핵심 로직
# -----------------------------------------------------------
def parse_ships_from_html(html_source, source_type="Web"):
    soup = BeautifulSoup(html_source, 'html.parser')
    table = soup.find('table', {'id': 'homeTable'})
    
    if not table:
        print(f"❌ [{source_type}] 테이블(id='homeTable')을 찾을 수 없습니다.")
        return []

    rows = table.find('tbody').find_all('tr')
    print(f"📊 [{source_type}] 원본 행 개수: {len(rows)}개")
    
    extracted_data = []
    scnt1 = 0 
    scnt2 = 0 
    scnt3 = 0 
    rcnt = 0 
    for row in rows:
        rcnt += 1
        cols = row.find_all('td')
        if len(cols) < 8: 
            scnt1 += 1
            continue # 데이터 컬럼 부족 시 스킵

        ship_id = None
        
        # 1. 해당 행(row) 안의 모든 span 중에서 type="button"이고 id가 있는 것을 찾습니다.
        #    (보통 Perf 컬럼이나 Name 컬럼 쪽에 숨어 있습니다)
        target_spans = row.find_all('span', {'type': 'button', 'id': True})
        
        for span in target_spans:
            # 2. 그 span의 부모가 div이고 class에 d-flex가 있는지 확인 (선택 사항이지만 정확도를 위해)
            #    사용자님 말씀대로 div 안의 구조인지 체크
            parent_div = span.find_parent('div')
            # if parent_div and 'd-flex' in parent_div.get('class', []): # 필요시 주석 해제하여 더 엄격하게 체크 가능
            
            # 3. [중요] span 안에 'a' 태그가 있는지 확인
            if span.find('a'):
                ship_id = span['id']
                break # 찾았으면 루프 종료
        
        # ID가 없으면(=링크가 없으면) 미구현 함선으로 간주하고 제외
        if not ship_id:
            scnt2 += 1
            continue
        
        # 2. 데이터 추출 및 정제
        # [Name Column] - Index 2
        full_name_text = cols[2].get_text(strip=True)
        # "첫 단어는 제조사, 나머지는 이름" 로직 적용
        name_parts = full_name_text.split(' ', 1)
        if len(name_parts) == 2:
            manufacturer = name_parts[0]
            ship_name = name_parts[1]
        else:
            manufacturer = "Unknown"
            ship_name = full_name_text
        # ship size 
        ship_size = cols[3].get_text(strip=True)
        # ship role
        role = cols[5].get_text(strip=True)

        # [Cargo Column] `- Index 4
        cargo_text = cols[4].get_text(strip=True)
        cargo_clean = re.sub(r'[^\d]', '', cargo_text) # 숫자만 남기기
        cargo_capacity = int(cargo_clean) if cargo_clean else 0

        if cargo_capacity == 0:
            scnt3 += 1
            continue  # 화물 용량이 0인 함선은 제외

        # [Price Columns] - Pledge (6), aUEC (7)
        pledge_price = cols[6].get_text(strip=True)
        auec_price = cols[7].get_text(strip=True)

        # 3. 최종 데이터 구조 (Haru-Logistics Spec)
        ship_entry = {
            ship_name : {
                "id": ship_id,
                "url": f"https://www.spviewer.eu/performance?ship={ship_id}",
                "manufacturer": manufacturer, # 제조사
                "name": ship_name,            # 함선명
                "size": ship_size,            # Size
                "cargo": cargo_capacity,      # Cargo
                "role": role, 
                "pledge": pledge_price,       # 서약 금액
                "auec": auec_price,           # 인게임 가격
            }
        }
        
        extracted_data.append(ship_entry)
    print(f"   - READ Count : {rcnt}개")
    print(f"   - 데이터 부복 스킵된 행 (컬럼 부족): {scnt1}개")
    print(f"   - 미구현 함선 스킵된 행 (ID/링크 없음): {scnt2}개")
    print(f"   - 화물 0 함선 스킵된 행: {scnt3}개")
    print(f"✅ [{source_type}] 추출 완료! 유효 함선 개수: {len(extracted_data)}개")    
    return extracted_data

# -----------------------------------------------------------
# [메인] 실행 로직 (Live -> Fail -> Local)
# -----------------------------------------------------------
final_ships_list = []

# 1. 라이브 스크래핑 시도
try:
    print("📡 [1단계] SPViewer 웹사이트 접속 시도...")
    chrome_options = Options()
    chrome_options.add_argument("--headless") # 화면 없이 실행
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://www.spviewer.eu/")
    
    print("⏳ 데이터 렌더링 대기 (30초)...")
    time.sleep(30)
    
    html_content = driver.page_source
    driver.quit()
    
    # 파싱 시도
    final_ships_list = parse_ships_from_html(html_content, "Web Live")

except Exception as e:
    print(f"⚠️ 웹 스크래핑 중 오류 발생: {e}")
    final_ships_list = [] # 오류 시 빈 리스트로 초기화

# 2. 실패 시 로컬 파일 로딩 (Fallback)
if len(final_ships_list) == 0:
    print("\n🚨 [2단계] 웹 데이터 없음. 'sssaa.html' 로컬 파일 로드로 전환합니다.")
    file_path = 'sssaa.html'
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                local_html = f.read()
            final_ships_list = parse_ships_from_html(local_html, "Local File")
        except Exception as e:
            print(f"❌ 로컬 파일 읽기 실패: {e}")
    else:
        print(f"❌ '{file_path}' 파일이 존재하지 않습니다.")

# -----------------------------------------------------------
# [결과] JSON 저장
# -----------------------------------------------------------
if final_ships_list:
    # 보기 좋게 제조사 -> 이름 순으로 정렬
    #final_ships_list.sort(key=lambda x: (x['manufacturer'], x['name']))
    
    output_file = 'master_ship.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_ships_list, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ 성공! 총 {len(final_ships_list)}개의 함선 데이터가 생성되었습니다.")
    print(f"💾 파일 저장 위치: {output_file}")
    
    # 데이터 미리보기
    df = pd.DataFrame(final_ships_list)
    print("\n[데이터 미리보기]")
    print(df[['manufacturer', 'name', 'cargo', 'role', 'pledge']].head())
else:
    print("\n❌ 데이터를 생성하지 못했습니다.")