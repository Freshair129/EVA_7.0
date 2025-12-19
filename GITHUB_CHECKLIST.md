# ⚠️ GITHUB UPLOAD CHECKLIST - READ THIS FIRST!

## 🔴 CRITICAL: ข้อมูลส่วนตัวที่พบในโปรเจค

### ไฟล์ที่มีข้อมูลส่วนตัว:

#### 1. **EVA_Soul/** folder
- `boss_soul_anchors.json` - มี L5 Year of Hell, mental health info
- `Genesis_Anchors.json` - มีชื่อคน, ความสัมพันธ์
- `Genesis_Memories.json` - อาจมีความทรงจำส่วนตัว
- `Boss_Soul_Layers_v5.md` - ข้อมูล mental state
- `EVA_Persona.md` - คำตอบ 70+ ข้อเกี่ยวกับตัวตน

#### 2. **Memory folders**
- `01_Episodic_memory/` - บันทึกการสนทนา
- `02_Semantic_memory/` - ความรู้ส่วนตัว
- `04_Session_Memory/` - session data
- `Buffer/` - temporary data

#### 3. **Logs**
- `ESS_logs/` - อาจมี debug info

---

## ✅ วิธีแก้: เลือก 1 ใน 4 วิธี

### **Option 1: Public Repo (แนะนำ)** ⭐
ลบข้อมูลส่วนตัว ใส่ template แทน

**ขั้นตอน:**
1. ลบไฟล์ส่วนตัว
2. ใส่ไฟล์ตัวอย่าง (template)
3. อัพเดท .gitignore
4. Push public repo

**ผลลัพธ์:**
- ✅ เพื่อนใช้ได้ทันที
- ✅ Community อาจมาช่วย
- ✅ ปลอดภัย 100%
- ❌ ไม่มี Boss Soul จริง (ใช้ template)

---

### **Option 2: Private Repo**
เก็บข้อมูลส่วนตัวไว้ แต่ repo เป็น private

**ขั้นตอน:**
1. สร้าง private repo
2. Push ทุกอย่าง (รวมข้อมูลส่วนตัว)
3. Invite เพื่อนเข้ามา

**ผลลัพธ์:**
- ✅ เก็บ Boss Soul จริง
- ✅ ควบคุมได้ว่าใครเข้าถึง
- ❌ ต้องจ่าย (GitHub ฟรี 3 collaborators)
- ❌ ไม่สามารถแชร์สาธารณะ

---

### **Option 3: Two Repos**
แยก public + private

**ขั้นตอน:**
1. **Public Repo:** Core system (ไม่มีข้อมูลส่วนตัว)
2. **Private Repo:** Boss Soul + Memory (ของคุณเอง)

**ผลลัพธ์:**
- ✅ Best of both worlds
- ✅ Public สำหรับ community
- ✅ Private สำหรับตัวเอง
- ❌ จัดการ 2 repos

---

### **Option 4: Local Git Only**
ไม่ขึ้น GitHub เลย, แชร์ผ่าน ZIP

**ขั้นตอน:**
1. git init (local only)
2. แชร์ ZIP file ให้เพื่อน

**ผลลัพธ์:**
- ✅ ควบคุมเต็มที่
- ❌ ไม่มี version control online
- ❌ แชร์ยาก

---

## 📋 ถ้าเลือก Option 1: Public Repo

### Checklist ก่อน Push:

#### ✅ ไฟล์ที่ต้องลบ/แทนที่:

```bash
# 1. ลบข้อมูลส่วนตัว
rm -rf EVA_Soul/
rm -f EVA_Persona.md
rm -rf 01_Episodic_memory/*
rm -rf 02_Semantic_memory/*
rm -rf 03_Sensory_memory/*
rm -rf 04_Session_Memory/*
rm -rf Buffer/*
rm -rf ESS_logs/*
rm -rf Backups/*

# 2. สร้าง template folders
mkdir -p EVA_Soul
mkdir -p 01_Episodic_memory
mkdir -p 02_Semantic_memory
mkdir -p 03_Sensory_memory

# 3. Copy template files (ที่เราจะสร้างให้)
# (see below)
```

#### ✅ ไฟล์ที่ปลอดภัย (push ได้):

- ✅ All Python code (*.py)
- ✅ Requirements, Docker files
- ✅ Documentation (CLAUDE.md, README.md, etc.)
- ✅ Config schemas (*.yaml, *.json schemas)
- ✅ Tests (test_*.py)
- ✅ .gitignore, LICENSE

#### ✅ .gitignore ต้องมี:

```gitignore
# Sensitive Data
.env
.env.*

# Personal Memory
01_Episodic_memory/*.json
!01_Episodic_memory/Episodic_memory_template.json
02_Semantic_memory/*.json
!02_Semantic_memory/Semantic_memory_template.json
03_Sensory_memory/*.json
04_Session_Memory/*
Buffer/
Backups/
ESS_logs/

# Personal Soul Data
EVA_Soul/*.json
!EVA_Soul/*_template.json
EVA_Soul/*.md
!EVA_Soul/README.md
```

---

## 🔒 Security Checklist

Before pushing to GitHub:

- [ ] ไม่มีไฟล์ `.env` (ถูก .gitignore)
- [ ] ไม่มี API keys ใน code
- [ ] ไม่มีชื่อจริง, อีเมล, เบอร์โทร
- [ ] ไม่มี passwords, credentials
- [ ] ไม่มีข้อมูล mental health
- [ ] ไม่มีข้อมูลความสัมพันธ์ส่วนตัว
- [ ] ลบ memory/logs ที่มีการสนทนาส่วนตัว

---

## 📝 ขั้นตอนแนะนำ (Option 1 - Public)

### 1. Backup ข้อมูลส่วนตัวก่อน!
```bash
# สำรองไว้ที่อื่น
cp -r "EVA 7.0" "EVA 7.0 - Personal Backup"
```

### 2. ลบข้อมูลส่วนตัว
```bash
cd "EVA 7.0"
# Run cleanup script (เราจะสร้างให้)
```

### 3. ใส่ Templates
```bash
# Copy template files (เราจะสร้างให้)
```

### 4. ทดสอบว่าทำงาน
```bash
python test_orchestrator_basic.py
# ต้อง PASS แม้ไม่มี Boss Soul จริง
```

### 5. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: EVA 7.0 - Public version"
git remote add origin <your-repo-url>
git push -u origin main
```

---

## 🎯 คำแนะนำของเรา

**สำหรับการแชร์สาธารณะ:**
→ ใช้ **Option 1** (Public Repo with Templates)

**สำหรับงานส่วนตัว:**
→ ใช้ **Option 2** (Private Repo) หรือ **Option 3** (Two Repos)

---

## 🆘 Need Help?

ถ้าไม่แน่ใจว่าไฟล์ไหนปลอดภัย:
1. เช็คว่ามีชื่อ, อีเมล, หรือข้อมูลส่วนตัวไหม
2. ถ้าไม่แน่ใจ → ลบออก
3. Better safe than sorry!

---

**Next:** ดู `GITHUB_SETUP.md` สำหรับขั้นตอน push
