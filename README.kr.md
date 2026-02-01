---

### 📄 2. `README.kr.md` (한국어 설명서)
한국어 사용자를 위한 상세 설명서입니다.

```markdown
# 🚀 MeloPugna Trade & Transport (TNT)

**스타시티즌 무역 및 화물 운송 최적화 솔루션**

MeloPugnaTNT는 스타시티즌의 화물 운송(Hauling) 미션과 무역을 효율적으로 관리하고, 최적의 이동 경로를 계산해 주는 도구입니다.

---

## ✨ 주요 기능

* **🚚 경로 시뮬레이션 (Route Sim):** 여러 건의 계약을 분석하여 최단/최적의 이동 경로를 자동으로 계산합니다.
    * *고급 설정 기능: 경유지 과부하 방지를 위해 시작/종료 지점 지정 가능*
* **📋 계약 관리 (Contract Manage):** 운송 계약을 추가, 수정, 삭제하고 리스트로 관리할 수 있습니다.
* **🚀 함선 관리 (Fleet Manager):** 마스터 DB를 기반으로 나의 보유 함선 목록과 적재량(SCU)을 관리합니다.
* **🗺️ 코드 매핑:** 장소와 물품 이름을 나만의 코드(A, B, 가, 나...)로 설정하여 빠르게 입력할 수 있습니다.
* **💾 설정 저장/불러오기:** 작업하던 모든 데이터(함선, 계약, 매핑 정보)를 JSON 파일로 저장하고 언제든 다시 불러올 수 있습니다.

---

## 🛠️ 설치 및 실행 방법

### 방법 1: 웹에서 바로 실행 (Streamlit Cloud)
이 프로젝트는 Streamlit Cloud에 최적화되어 있습니다.
1.  이 저장소(Repository)를 본인 계정으로 Fork 합니다.
2.  Streamlit Cloud에서 'New App'을 생성합니다.
3.  **중요:** 설정에서 `Main file path`를 반드시 **`main.py`** 로 지정해 주세요.

### 방법 2: 내 컴퓨터에서 실행
1.  **프로젝트 다운로드:**
    ```bash
    git clone [https://github.com/본인아이디/MeloPugnaTNT.git](https://github.com/본인아이디/MeloPugnaTNT.git)
    cd MeloPugnaTNT
    ```
2.  **필요 프로그램 설치:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **앱 실행:**
    ```bash
    streamlit run main.py
    ```

---

## 📂 폴더 구조

* **`main.py`**: 프로그램 시작 파일
* **`modules/`**: 화면(UI)을 구성하는 파일들 (계약 추가, 관리, 시뮬레이션 탭)
* **`utils/`**: 핵심 계산 로직, 데이터 저장/로드, 버전 관리
* **`data/`**: 함선 정보 데이터베이스 (JSON)

---

## 📜 라이선스 및 정보
이 프로그램은 **Star Citizen** 팬 메이드 툴입니다.
**제작:** MeloPugna
**기술 지원:** Google Gemini