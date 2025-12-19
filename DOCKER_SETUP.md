# EVA 7.0 - Docker Setup Guide

## ทำไมต้อง Docker?

✅ **ข้อดี:**
- ไม่ต้องติดตั้ง Python (Docker จัดการให้)
- Environment เหมือนกัน 100% ทุกเครื่อง
- แยก isolation จากระบบ
- Deploy ง่าย (Cloud, Server)
- Version control ระบบทั้งหมด

❌ **ข้อเสีย:**
- ต้องติดตั้ง Docker (~500MB)
- ช้ากว่าการ run ตรง
- ซับซ้อนกว่าแบบปกติ

**คำแนะนำ:** ถ้าแค่ให้เพื่อนเทส ใช้ **SETUP.md (วิธีปกติ)** ง่ายกว่า!

---

## ความต้องการ

- Docker Desktop (Windows/Mac) หรือ Docker Engine (Linux)
- 2GB RAM ว่าง
- 5GB disk space
- Google API Key

---

## ติดตั้ง Docker

### Windows/Mac:
1. ดาวน์โหลด: https://www.docker.com/products/docker-desktop
2. ติดตั้ง Docker Desktop
3. เปิด Docker Desktop
4. รอจนขึ้น "Docker Desktop is running"

### Linux:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Logout/Login again
```

ตรวจสอบ:
```bash
docker --version
docker-compose --version
```

---

## Setup EVA 7.0 ด้วย Docker

### 1. Clone โปรเจค
```bash
git clone <your-repo-url>
cd "EVA 7.0"
```

### 2. สร้างไฟล์ `.env`
```bash
# Windows
echo GOOGLE_API_KEY=your_api_key_here > .env

# macOS/Linux
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

### 3. Build Docker Image
```bash
docker-compose build
```
ใช้เวลา 2-5 นาที (ครั้งแรก)

### 4. Run Container
```bash
# Run test (default)
docker-compose up

# Run แบบ background
docker-compose up -d

# Run orchestrator
docker-compose run eva python Orchestrator/two_phase_orchestrator.py

# Run specific test
docker-compose run eva python integration_demo.py
```

---

## คำสั่งที่ใช้บ่อย

### ดู Container ที่กำลังทำงาน
```bash
docker-compose ps
```

### ดู Logs
```bash
docker-compose logs -f
```

### Stop Container
```bash
docker-compose down
```

### Rebuild หลังแก้โค้ด
```bash
docker-compose build --no-cache
docker-compose up
```

### เข้าไปใน Container (Interactive)
```bash
docker-compose run --rm eva bash

# ใน container:
python integration_demo.py
python test_orchestrator_basic.py
exit  # ออกจาก container
```

### ลบทุกอย่าง (Reset)
```bash
docker-compose down -v --rmi all
```

---

## โครงสร้าง Docker

```
EVA 7.0/
├── Dockerfile              # Image definition
├── docker-compose.yml      # Service configuration
├── .env                   # API key (ห้าม commit!)
├── .dockerignore          # ไฟล์ที่ไม่เอาเข้า image
└── requirements.txt       # Python dependencies
```

**ข้างใน Container:**
- Python 3.11
- EVA 7.0 code
- Dependencies ครบ
- Logs → ถูก mount ออกมาข้างนอก
- Memory → ถูก mount ออกมาข้างนอก

---

## Volumes (Data Persistence)

Docker mount folders เหล่านี้ออกมา:
- `01_Episodic_memory/` - Episodic memory
- `02_Semantic_memory/` - Semantic memory
- `03_Sensory_memory/` - Sensory memory
- `07_User_block/` - User facts
- `ESS_logs/` - ESS logs
- `Backups/` - MSP backups

**ข้อดี:** ข้อมูลไม่หายแม้ลบ container

---

## Development Workflow

### 1. แก้โค้ด (ในเครื่อง)
```bash
# แก้ไฟล์ .py ต่างๆ
```

### 2. Test ด้วย Docker
```bash
# Option A: Build ใหม่ทุกครั้ง (slow แต่แน่ใจ)
docker-compose build
docker-compose up

# Option B: Mount code เข้าไป (fast)
docker-compose run -v "$(pwd):/app" eva python your_test.py
```

### 3. ถ้าเพิ่ม dependency
```bash
# เพิ่มใน requirements.txt
echo "new-package>=1.0.0" >> requirements.txt

# Rebuild
docker-compose build
```

---

## Troubleshooting

### ❌ "Cannot connect to Docker daemon"
- เปิด Docker Desktop
- รอให้ status เป็น "Running"

### ❌ "Port already in use"
```bash
# ดูว่า port ถูกใช้โดยใคร
docker ps

# หยุด container เก่า
docker-compose down
```

### ❌ "No such file or directory: .env"
```bash
# สร้างไฟล์ .env
echo "GOOGLE_API_KEY=your_key" > .env
```

### ❌ "Image build failed"
```bash
# ลอง build แบบไม่ใช้ cache
docker-compose build --no-cache

# หรือเช็ค error ใน Dockerfile
```

### ❌ Container หยุดทำงานทันที
```bash
# ดู logs
docker-compose logs

# Run แบบ interactive
docker-compose run eva bash
```

### ❌ "Out of disk space"
```bash
# ลบ images/containers ที่ไม่ใช้
docker system prune -a
```

---

## Deploy to Cloud

### Docker Hub (แชร์ image)
```bash
# Build
docker build -t your-username/eva-7.0:latest .

# Push
docker login
docker push your-username/eva-7.0:latest

# เพื่อนของคุณ pull
docker pull your-username/eva-7.0:latest
docker run -e GOOGLE_API_KEY=their_key your-username/eva-7.0
```

### Google Cloud Run
```bash
# Build for Cloud Run
gcloud builds submit --tag gcr.io/your-project/eva-7.0

# Deploy
gcloud run deploy eva --image gcr.io/your-project/eva-7.0 \
  --set-env-vars GOOGLE_API_KEY=your_key
```

---

## Environment Variables

ใน `.env` file:
```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional
# GEMINI_API_KEY=alternative_key
# LOG_LEVEL=DEBUG
# MSP_VALIDATION_MODE=strict
```

**CRITICAL:** อย่า commit `.env` ขึ้น Git!

---

## Security Best Practices

1. **Never commit `.env`**
   - ใช้ `.gitignore`
   - แชร์ `.env.example` แทน

2. **Use Docker secrets (production)**
   ```bash
   echo "your_api_key" | docker secret create google_api_key -
   ```

3. **Limit resources**
   - ตั้ง CPU/Memory limits ใน `docker-compose.yml`

4. **Run as non-root** (advanced)
   ```dockerfile
   USER 1000:1000
   ```

---

## Performance Tips

### 1. Multi-stage builds (ใน Dockerfile แล้ว)
- Builder stage: install dependencies
- Runtime stage: copy เฉพาะที่จำเป็น
- ผลลัพธ์: Image เล็กกว่า

### 2. Layer caching
```dockerfile
# Copy requirements first (changes น้อย)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code later (changes บ่อย)
COPY . .
```

### 3. .dockerignore
```
__pycache__
*.pyc
.git
.venv
```

---

## เปรียบเทียบ: Setup ปกติ vs Docker

| Feature | Setup ปกติ | Docker |
|---------|-----------|--------|
| Setup Time | 5 นาที | 10-15 นาที |
| Disk Space | ~500 MB | ~2 GB |
| Performance | เร็ว | ช้ากว่าเล็กน้อย |
| Isolation | ❌ | ✅ |
| Portability | 🟡 | ✅✅ |
| Complexity | ง่าย | ซับซ้อน |
| Deploy | ยาก | ง่าย |

**คำแนะนำ:**
- **ให้เพื่อนเทส:** ใช้ Setup ปกติ (`SETUP.md`)
- **Deploy Production:** ใช้ Docker
- **Share กับหลายคน:** ใช้ Docker
- **Development:** Setup ปกติเร็วกว่า

---

## สรุป

**Quick Start:**
```bash
# 1. สร้าง .env
echo "GOOGLE_API_KEY=your_key" > .env

# 2. Build & Run
docker-compose up
```

**อยากรู้เพิ่ม:**
- Docker Docs: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/

---

**หมายเหตุ:** ถ้าแค่ testing ง่ายๆ → ใช้ `SETUP.md` ดีกว่า!
