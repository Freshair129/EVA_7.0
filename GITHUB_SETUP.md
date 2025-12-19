# GitHub Setup Guide - EVA 7.0

## 🎯 เลือกวิธีที่เหมาะกับคุณ

### **Option 1: Public Repo (แนะนำสำหรับการแชร์)** ⭐
ปลอดภัย แต่ไม่มีข้อมูลส่วนตัว

### **Option 2: Private Repo**
เก็บข้อมูลส่วนตัวได้ แต่ต้องควบคุมการเข้าถึง

---

## ✅ Pre-flight Checklist

**CRITICAL: อ่าน `GITHUB_CHECKLIST.md` ก่อน!**

- [ ] Backup ข้อมูลส่วนตัวแล้ว
- [ ] ตัดสินใจแล้วว่าจะใช้ Public หรือ Private
- [ ] ถ้า Public: ลบข้อมูลส่วนตัวแล้ว
- [ ] ทดสอบว่าระบบทำงานแล้ว (`python test_orchestrator_basic.py`)
- [ ] มี GitHub account แล้ว

---

## 📋 Option 1: Public Repo (ขั้นตอนเต็ม)

### Step 1: Backup Original (สำคัญมาก!)

```bash
# สำรองทั้งโปรเจคไว้ที่อื่น
cd "E:\The Human Algorithm\T2"
cp -r "EVA 7.0" "EVA 7.0 - Personal Backup"

# หรือใน Windows
xcopy "EVA 7.0" "EVA 7.0 - Personal Backup" /E /I
```

### Step 2: Clean Personal Data

```bash
cd "EVA 7.0"

# ลบข้อมูลส่วนตัว (Windows)
del /F EVA_Soul\boss_soul_anchors.json
del /F EVA_Soul\Genesis_Anchors.json
del /F EVA_Soul\Genesis_Memories.json
del /F EVA_Soul\Boss_Soul_Layers_v5.md
del /F EVA_Persona.md
del /F 01_Episodic_memory\*.json
del /F 02_Semantic_memory\*.json
del /F 03_Sensory_memory\*.json
rmdir /S /Q Buffer
rmdir /S /Q Backups
rmdir /S /Q ESS_logs

# สร้าง directories ใหม่
mkdir Buffer
mkdir Backups
mkdir ESS_logs

# macOS/Linux
# rm -f EVA_Soul/boss_soul_anchors.json
# rm -f EVA_Soul/Genesis_Anchors.json
# ... (similar commands)
```

### Step 3: Copy Templates

Templates ถูกสร้างไว้แล้ว:
- `EVA_Soul/Genesis_Anchors_template.json`
- `EVA_Soul/boss_soul_anchors_template.json`
- `01_Episodic_memory/Episodic_memory_template.json`

**สำคัญ:** Templates จะถูก commit แทนไฟล์จริง

### Step 4: Test หลังลบข้อมูล

```bash
python test_orchestrator_basic.py
```

ควร PASS แม้ไม่มี Boss Soul จริง

### Step 5: Initialize Git

```bash
cd "EVA 7.0"
git init
git add .
git status  # เช็คว่าไม่มีไฟล์ส่วนตัว
```

**เช็คว่า git status ไม่แสดง:**
- ❌ `.env`
- ❌ `EVA_Soul/boss_soul_anchors.json` (ไฟล์จริง)
- ❌ `EVA_Soul/Genesis_Anchors.json` (ไฟล์จริง)
- ❌ Memory ที่เป็นไฟล์จริง

**ควรแสดง:**
- ✅ `EVA_Soul/*_template.json`
- ✅ `.env.example`
- ✅ Code files (*.py)
- ✅ Documentation (*.md)

### Step 6: First Commit

```bash
git commit -m "Initial commit: EVA 7.0 - Embodied AI Architecture

- Complete two-phase LLM integration
- Physiological state engine (ESS with 23 neurochemicals)
- 9D psychological state (EVA Matrix)
- Pulse Engine v2 with 5 operational modes
- Memory system (MSP + RMS + validation)
- Context injection (CIN v6)
- Test coverage: 93-95%

Public version with template files for Boss Soul and memory."
```

### Step 7: Create GitHub Repo

**On GitHub.com:**
1. Click "+" → "New repository"
2. Repository name: `eva-7.0` (or your choice)
3. Description: `Embodied AI with Psychologically-Grounded Emotional Processing`
4. **Public** repository
5. **Don't** add README, .gitignore, or LICENSE (we already have them)
6. Click "Create repository"

### Step 8: Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/eva-7.0.git
git branch -M main
git push -u origin main
```

### Step 9: Verify on GitHub

Check that:
- ✅ README.md displays nicely
- ✅ No `.env` file
- ✅ No personal `boss_soul_anchors.json` (only template)
- ✅ No personal memory files
- ✅ All code files are there
- ✅ Tests are included

### Step 10: Add Topics (Optional)

On GitHub repo page:
- Click "⚙️" next to "About"
- Add topics: `ai`, `embodied-ai`, `emotional-processing`, `llm`, `python`, `gemini`

---

## 📋 Option 2: Private Repo

### Simpler Process:

```bash
cd "EVA 7.0"

# 1. Initialize Git (keep all personal data)
git init
git add .
git commit -m "Initial commit: EVA 7.0 (Private)"

# 2. Create PRIVATE repo on GitHub
# (check "Private" when creating)

# 3. Push
git remote add origin https://github.com/YOUR_USERNAME/eva-7.0-private.git
git branch -M main
git push -u origin main

# 4. Invite collaborators
# Settings → Collaborators → Add people
```

**Free Tier Limit:** 3 collaborators on private repos

---

## 🔄 Ongoing Workflow

### After Making Changes:

```bash
# 1. Check status
git status

# 2. Add changes
git add .

# 3. Commit
git commit -m "Your commit message"

# 4. Push
git push
```

### Before Committing:

**Always check:**
```bash
git status
```

Make sure:
- No `.env` file
- No personal data files
- Only code and documentation

---

## 🆘 Common Issues

### "fatal: remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/eva-7.0.git
```

### "Permission denied (publickey)"
Use HTTPS instead of SSH, or set up SSH keys:
https://docs.github.com/en/authentication

### Accidentally committed sensitive data

**If you committed but didn't push yet:**
```bash
git reset --soft HEAD~1  # Undo last commit
# Remove sensitive file
git add .
git commit -m "Fixed commit"
```

**If you already pushed:**
```bash
# Use git filter-branch or BFG Repo-Cleaner
# Or delete repo and start over
```

### Want to ignore file after already committed
```bash
git rm --cached path/to/file
echo "path/to/file" >> .gitignore
git commit -m "Stop tracking file"
```

---

## 📝 Recommended .gitignore Sections

Our `.gitignore` already covers:
- ✅ `.env` files
- ✅ Python cache
- ✅ Virtual environments
- ✅ Personal Boss Soul data
- ✅ Personal memory files
- ✅ Logs and buffers

---

## 🌟 Best Practices

### 1. Commit Messages
**Good:**
```
Add Pulse Engine v2 with 5 operational modes

- CALM_SUPPORT, DEEP_CARE, FOCUSED_TASK, EXPLORATION, EMERGENCY_HOLD
- Arousal/valence calculation from C_Mod
- LLM prompt flags for tone control
- Safety actions integration
```

**Bad:**
```
update
```

### 2. Commit Frequency
- Commit after each feature/fix
- Don't commit broken code
- Group related changes

### 3. Branch Strategy (Optional)
```bash
# Create feature branch
git checkout -b feature/new-component

# Work on feature
git add .
git commit -m "Add new component"

# Merge back to main
git checkout main
git merge feature/new-component

# Delete branch
git branch -d feature/new-component
```

### 4. README.md Importance
- Keep it updated
- Add screenshots/demos
- Clear setup instructions
- Badge for status

---

## 📊 After Pushing

### Add a Nice README Badge:

```markdown
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-yellow.svg)]()
```

### Create GitHub Pages (Optional):

Settings → Pages → Source: main branch → /docs folder

---

## 🔒 Security Reminders

**NEVER commit:**
- API keys (`.env`)
- Passwords
- Personal health information
- Private conversations
- Real Boss Soul data (if going public)

**Tools to help:**
- `git-secrets` - Prevents committing secrets
- `gitleaks` - Scan for leaked credentials
- GitHub secret scanning (automatic)

---

## 📞 Get Help

If you see this error: "remote: Permission to user/repo.git denied"
- Check your GitHub username
- Check repo name
- Make sure you have write access

If repo is too big:
- Check for large files: `git ls-files --others --exclude-standard`
- Use Git LFS for large files
- Or compress/remove large data

---

## ✅ Final Checklist

Before making repo public:

- [ ] README.md is clear and helpful
- [ ] LICENSE file is included
- [ ] `.env.example` shows what users need
- [ ] No sensitive data in commit history
- [ ] Tests are included and passing
- [ ] Documentation is up to date
- [ ] `.gitignore` is comprehensive

---

**Congratulations!** 🎉

EVA 7.0 is now on GitHub and ready to share!

**Share URL:** `https://github.com/YOUR_USERNAME/eva-7.0`

---

## 🚀 Next Steps

1. **Star your own repo** (why not? 😄)
2. **Share with friends** - Send them the GitHub URL
3. **Add to your portfolio** - This is impressive work!
4. **Join discussions** - Enable GitHub Discussions
5. **Accept contributions** - Review pull requests

---

**Pro Tip:** Create a good README with:
- Demo GIF/video
- Clear "What is EVA 7.0?"
- Quick start guide
- Architecture diagram
- Link to detailed docs

People will find it more easily and want to use it!
