# 🚀 MeloPugna Trade & Transport (TNT)

**Star Citizen Trade & Cargo Hauling Optimization Solution**

MeloPugnaTNT is a powerful tool designed to help Star Citizen haulers optimize their trade routes, manage contracts, and organize their fleet efficiently. Built with Python and Streamlit.

---

## ✨ Key Features

* **🚚 Route Simulation:** innovative pathfinding algorithm to calculate the most efficient trade routes based on multiple contracts.
    * *Includes "Advanced Options" to specify start/end points for performance optimization.*
* **📋 Contract Management:** Easily add, edit, and track your trade contracts and missions.
* **🚀 Fleet Manager:** Manage your personal fleet specifications (Cargo capacity, size, etc.) integrated with a Master Ship Database.
* **🗺️ Custom Mapping:** Map in-game location codes and item names to your preference.
* **💾 Save & Load:** Export your configuration (fleet, missions, settings) to a JSON file and load it anytime (Data Persistence).
* **🌐 Multi-Language Support:** Fully localized for **English** and **Korean**.

---

## 🛠️ Installation & Usage

### Option 1: Streamlit Cloud (Recommended)
This project is optimized for [Streamlit Cloud](https://streamlit.io/cloud).
1.  Fork this repository.
2.  Deploy on Streamlit Cloud.
3.  **Important:** Set the `Main file path` to **`main.py`** in the settings.

### Option 2: Local Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_ID/MeloPugnaTNT.git](https://github.com/YOUR_ID/MeloPugnaTNT.git)
    cd MeloPugnaTNT
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the application:**
    ```bash
    streamlit run main.py
    ```

---

## 📂 Project Structure

```text
MeloPugnaTNT/
├── main.py               # Application Entry Point
├── modules/              # UI Components (Sidebar, Tabs)
├── utils/                # Logic, Data Manager, Constants
├── data/                 # Master Data (JSON)
└── requirements.txt      # Python Dependencies