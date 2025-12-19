# EVA 7.0 - Quick Setup Guide

## วิธีที่ 1: Setup แบบง่าย (แนะนำ) ⭐

### ความต้องการ
- Python 3.9 หรือสูงกว่า
- Git (สำหรับ clone โปรเจค)
- Google API Key (ฟรี)

---

### ขั้นตอน Setup (Windows)

#### 1. Clone โปรเจค
```bash
git clone <your-repo-url>
cd "EVA 7.0"
```

#### 2. สร้าง Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

#### 3. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

#### 4. ตั้งค่า API Key
สร้างไฟล์ `.env` ที่ root folder:
```bash
echo GOOGLE_API_KEY=your_api_key_here > .env
```

**วิธีขอ API Key (ฟรี):**
1. ไปที่: https://makersuite.google.com/app/apikey
2. คลิก "Create API Key"
3. Copy key มาใส่ในไฟล์ `.env`

---

### ทดสอบว่าทำงาน

#### Test 1: Core Pipeline (ไม่ต้อง API key)
```bash
python integration_demo.py
```
ควรเห็น output แบบนี้:
```
[Pipeline] Initializing EVA components...
[EHM] Loaded 23 chemicals
[EVAMatrix9D] Engine initialized and ready.
...
PIPELINE COMPLETE
```

#### Test 2: EVA Tool (ไม่ต้อง API key)
```bash
python test_orchestrator_basic.py
```
ควรเห็น:
```
ALL TESTS PASSED [OK]
```

#### Test 3: Orchestrator กับ LLM (ต้อง API key)
```bash
cd Orchestrator
python two_phase_orchestrator.py
```
ควรเห็น EVA ตอบโต้ได้จริง!

---

### ขั้นตอน Setup (macOS/Linux)

#### 1-3. เหมือน Windows แต่ activate venv ต่างกัน:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. ตั้งค่า API Key:
```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

---

### โครงสร้าง Folder

```
EVA 7.0/
├── .env                           # API key (สร้างเอง)
├── requirements.txt               # Dependencies
├── integration_demo.py            # Test core pipeline
├── test_orchestrator_basic.py    # Test orchestrator
│
├── ESS_Emotive_Signaling_System/  # Hormone system
├── EVA_Metric/                    # EVA Matrix, RI, RIM
├── Artifact_Qualia/               # Phenomenology
├── Resonance_Memory_System/       # Memory encoding
├── Pulse/                         # Pulse Engine
├── Memory_&_Soul_Passaport/       # MSP + Validation
│
└── Orchestrator/                  # LLM Integration
    ├── eva_tool.py               # Unified tool
    ├── two_phase_orchestrator.py # Main orchestrator
    ├── llm_bridge.py             # Gemini API
    └── CIN/                      # Context injection
```

---

### คำสั่งที่ใช้บ่อย

**เปิด venv:**
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

**ปิด venv:**
```bash
deactivate
```

**ติดตั้ง package เพิ่มเติม:**
```bash
pip install <package-name>
pip freeze > requirements.txt  # อัพเดท requirements
```

---

### Troubleshooting

#### ❌ "No module named 'google.generativeai'"
```bash
pip install google-generativeai
```

#### ❌ "CRITICAL: No API Key found"
- ตรวจสอบว่าไฟล์ `.env` อยู่ที่ root folder
- ตรวจสอบว่าข้างในมี: `GOOGLE_API_KEY=...`
- Restart terminal/script

#### ❌ "Python version too old"
```bash
python --version  # ต้อง 3.9+
```
อัพเดท Python จาก: https://www.python.org/downloads/

#### ❌ "Import error" แบบอื่นๆ
```bash
pip install -r requirements.txt --upgrade
```

---

### หยุดการทำงาน

กด `Ctrl+C` ใน terminal

---

### ลบ Environment (ถ้าต้องการ reset)

```bash
# Windows
rmdir /s venv

# macOS/Linux
rm -rf venv
```

แล้ว setup ใหม่ตั้งแต่ขั้นตอนที่ 2

---

## วิธีที่ 2: Docker (สำหรับ Advanced Users)

ดู `DOCKER_SETUP.md` (coming soon)

---

**หมายเหตุ:**
- ไฟล์ `.env` **อย่า** commit ขึ้น Git (มี API key)
- ใช้ `.gitignore` กัน
- แชร์โปรเจคผ่าน ZIP หรือ Git repository
- เพื่อนต้องขอ API key เองที่ Google AI Studio

---

**Need help?**
- ดู `CLAUDE.md` สำหรับ architecture details
- ดู `DONE.md` สำหรับ feature list
- ดู test files สำหรับ usage examples
