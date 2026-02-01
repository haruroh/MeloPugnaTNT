import json
import os

# 파일 경로 설정
input_path = "tmp/master_ship_20260131.json"
output_path = "tmp/master_ship.json" # 안전을 위해 새 파일로 저장

def fix_ship_data():
    if not os.path.exists(input_path):
        print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
        return

    try:
        with open(input_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        # 변환 로직
        new_db = {}
        
        if isinstance(data, list):
            print(f"ℹ️ 리스트 형식 감지됨. ({len(data)}개 항목)")
            for item in data:
                # item은 {"Avenger Titan": {...}} 형태임
                # update를 쓰면 딕셔너리를 합칠 수 있음
                new_db.update(item)
        elif isinstance(data, dict):
            print("ℹ️ 이미 올바른 딕셔너리 형식입니다.")
            new_db = data
        
        # 저장
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(new_db, f, indent=4, ensure_ascii=False)
            
        print(f"✅ 변환 완료! '{output_path}' 파일이 생성되었습니다.")
        print(f"📊 총 {len(new_db)}개의 함선 데이터가 정리되었습니다.")
        print("👉 확인 후 파일명을 'master_ship.json'으로 변경하여 사용하세요.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    fix_ship_data()